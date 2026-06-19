// v4
import { createClient } from "npm:@supabase/supabase-js@2";
import {
  buildLinePushPayload,
  inferLineMessageType,
  lineAccessTokenEnvForChannel,
  sendLinePush,
  sendLineReply,
} from "./line_send.ts";
import {
  buildConversationRef,
  buildNormalizedJob,
  extractLineEventIdentity,
  isPostgresUniqueViolation,
  redactLineEventForStorage,
  resolveLineChannel,
  senderTypeForChannel,
  sha256Base64,
  verifyLineSignature,
} from "./line_webhook.ts";
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-line-signature, x-impact-webhook-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
Deno.serve(async (req) => {
  const url = new URL(req.url);
  if (req.method === "OPTIONS") {
    return jsonResponse({
      ok: true,
    }, 200);
  }
  if (req.method !== "POST") {
    return jsonResponse({
      ok: false,
      error: "method_not_allowed",
    }, 405);
  }
  if (
    url.pathname === "/line/send-text" ||
    url.pathname.endsWith("/line/send-text") ||
    url.pathname === "/line/send-message" ||
    url.pathname.endsWith("/line/send-message")
  ) {
    return await handleLineTextSend(req);
  }
  const channel = resolveLineChannel(url, Deno.env.get("LINE_DEFAULT_CHANNEL"));
  if (!channel) {
    return jsonResponse({
      ok: false,
      error: "missing_or_invalid_line_channel",
    }, 400);
  }
  const channelSecret = getLineChannelSecret(channel);
  if (!channelSecret) {
    return jsonResponse({
      ok: false,
      error: "missing_line_channel_secret",
    }, 500);
  }
  const rawBody = await req.text();
  const signature = req.headers.get("x-line-signature");
  const signatureIsValid = await verifyLineSignature(
    rawBody,
    channelSecret,
    signature,
  );
  if (!signatureIsValid) {
    return jsonResponse({
      ok: false,
      error: "invalid_line_signature",
    }, 401);
  }
  let payload;
  try {
    payload = JSON.parse(rawBody);
  } catch {
    return jsonResponse({
      ok: false,
      error: "invalid_json",
    }, 400);
  }
  const events = Array.isArray(payload.events) ? payload.events : [];
  const supabase = createSupabaseClient();
  const results = [];
  for (const event of events) {
    results.push(
      await persistAndDispatchEvent({
        supabase,
        channel,
        event,
        rawEvent: event,
      }),
    );
  }
  const dispatched = results.filter((result) =>
    result.status === "dispatched"
  ).length;
  const deduped =
    results.filter((result) => result.status === "deduped").length;
  const failed = results.filter((result) => result.status === "failed").length;
  return jsonResponse({
    ok: failed === 0,
    channel,
    received: events.length,
    dispatched,
    deduped,
    failed,
    results,
  }, failed === 0 ? 200 : 207);
});
async function persistAndDispatchEvent(input) {
  const identity = extractLineEventIdentity(input.event);
  const correlationId = crypto.randomUUID();
  const receivedAt = new Date().toISOString();
  const conversationRef = buildConversationRef(
    input.channel,
    input.event.source,
  );
  const { data: conversation, error: conversationError } = await input.supabase
    .from("conversations").upsert({
      channel: input.channel,
      channel_conversation_ref: conversationRef,
      line_user_id: identity.lineUserId,
      status: "open",
    }, {
      onConflict: "channel,channel_conversation_ref",
    }).select("id, booking_id").single();
  if (conversationError) {
    return {
      status: "failed",
      error: conversationError.message,
    };
  }
  const replyToken = typeof input.event.replyToken === "string"
    ? input.event.replyToken
    : null;
  const replyTokenHash = replyToken ? await sha256Base64(replyToken) : null;
  const eventRow = {
    line_webhook_event_id: identity.lineWebhookEventId,
    line_delivery_is_redelivery: identity.isRedelivery,
    line_channel: input.channel,
    line_source_type: identity.sourceType,
    line_user_id: identity.lineUserId,
    line_group_id: identity.lineGroupId,
    line_room_id: identity.lineRoomId,
    event_type: identity.eventType,
    message_id: identity.messageId,
    reply_token_hash: replyTokenHash,
    raw_payload: redactLineEventForStorage(input.rawEvent),
    processing_status: "received",
    correlation_id: correlationId,
    conversation_id: conversation.id,
    received_at: receivedAt,
  };
  const { data: webhookEvent, error: insertEventError } = await input.supabase
    .from("line_webhook_events").insert(eventRow).select("id, correlation_id")
    .single();
  if (isPostgresUniqueViolation(insertEventError)) {
    return {
      status: "deduped",
      line_webhook_event_id: identity.lineWebhookEventId,
    };
  }
  if (insertEventError) {
    return {
      status: "failed",
      error: insertEventError.message,
    };
  }
  let messageId = null;
  if (identity.eventType === "message" || identity.eventType === "postback") {
    const msgType = identity.eventType === "postback"
      ? "text"
      : normalizeMessageType(identity.messageType);
    const bodyVal = identity.eventType === "postback"
      ? (input.event.postback?.displayText ?? identity.messageText)
      : identity.messageText;
    const { data: message, error: messageError } = await input.supabase.from(
      "conversation_messages",
    ).insert({
      conversation_id: conversation.id,
      line_webhook_event_id: webhookEvent.id,
      provider_event_id: identity.messageId ?? identity.lineWebhookEventId,
      correlation_id: webhookEvent.correlation_id,
      sender_type: senderTypeForChannel(input.channel),
      sender_ref: identity.lineUserId ?? identity.lineGroupId ??
        identity.lineRoomId,
      channel: input.channel,
      message_type: msgType,
      body: bodyVal,
      payload: identity.eventType === "postback"
        ? (input.event.postback ?? {})
        : (input.event.message ?? {}),
      direction: "inbound",
      visibility: input.channel === "housekeeping_line"
        ? "housekeeping"
        : "internal",
      contains_personal_data: input.channel === "guest_oa",
    }).select("id").single();
    if (messageError) {
      await markWebhookEventFailed(
        input.supabase,
        webhookEvent.id,
        messageError.message,
      );
      return {
        status: "failed",
        source_event_id: webhookEvent.id,
        error: messageError.message,
      };
    }
    messageId = message.id;
  }
  const job = buildNormalizedJob({
    correlationId: webhookEvent.correlation_id,
    sourceEventId: webhookEvent.id,
    lineChannel: input.channel,
    event: input.event,
    conversationId: conversation.id,
    bookingId: conversation.booking_id,
    receivedAt,
  });
  const dispatchResult = await dispatchToN8n(job);
  if (!dispatchResult.ok) {
    await markWebhookEventFailed(
      input.supabase,
      webhookEvent.id,
      dispatchResult.error,
    );
    return {
      status: "failed",
      source_event_id: webhookEvent.id,
      conversation_message_id: messageId,
      error: dispatchResult.error,
    };
  }
  await input.supabase.from("line_webhook_events").update({
    processing_status: "dispatched",
    normalized_job: job,
    processed_at: new Date().toISOString(),
  }).eq("id", webhookEvent.id);
  return {
    status: "dispatched",
    source_event_id: webhookEvent.id,
    conversation_id: conversation.id,
    conversation_message_id: messageId,
    correlation_id: webhookEvent.correlation_id,
  };
}
const SUPPRESSED_GUEST_PLACEHOLDER = "ขออภัยค่ะ ขอให้ทีมงานตรวจสอบก่อนตอบกลับนะคะ";

async function buildSuppressedOutboundPayload(
  recipient: string,
  body: Record<string, unknown>,
  originalText: string,
  originalTexts: string[],
  originalImages: unknown[],
) {
  let originalTextHash = null;
  if (originalText.trim()) {
    const encoder = new TextEncoder();
    const digest = await crypto.subtle.digest(
      "SHA-256",
      encoder.encode(originalText),
    );
    originalTextHash = Array.from(new Uint8Array(digest))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  const suppressionMetadata = {
    status: "suppressed",
    reason: typeof body.suppression_reason === "string"
      ? body.suppression_reason
      : "internal_review_required",
    source: "line-webhook-gateway",
    original_text_present: originalText.trim().length > 0,
    original_text_hash: originalTextHash,
    original_text_length: originalText.length,
    original_image_count: originalImages.length,
    model_recommended_mode: typeof body.model_recommended_mode === "string"
      ? body.model_recommended_mode
      : null,
    final_delivery_mode: typeof body.final_delivery_mode === "string"
      ? body.final_delivery_mode
      : null,
    risk_family: typeof body.risk_family === "string" ? body.risk_family : null,
    risk_subtype: typeof body.risk_subtype === "string"
      ? body.risk_subtype
      : null,
    alert_kind: typeof body.alert_kind === "string" ? body.alert_kind : null,
  };

  return {
    to: recipient,
    messages: [
      {
        type: "text",
        text: SUPPRESSED_GUEST_PLACEHOLDER,
      },
    ],
    suppression: suppressionMetadata,
  };
}

async function handleLineTextSend(req) {
  const expectedSecret = Deno.env.get("N8N_WEBHOOK_SECRET");
  const receivedSecret = req.headers.get("x-impact-webhook-secret");
  if (!expectedSecret || receivedSecret !== expectedSecret) {
    return jsonResponse({
      ok: false,
      error: "invalid_internal_secret",
    }, 401);
  }
  let body;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({
      ok: false,
      error: "invalid_json",
    }, 400);
  }
  const channel = parseLineChannel(body.channel);
  if (!channel) {
    return jsonResponse({
      ok: false,
      error: "missing_or_invalid_line_channel",
    }, 400);
  }
  const recipient = typeof body.to === "string" ? body.to : "";
  const rawMessages = body.messages === undefined ? undefined : body.messages;
  const legacyText = typeof body.text === "string" ? body.text : undefined;
  const legacyTexts = Array.isArray(body.texts)
    ? body.texts.filter((message) => typeof message === "string")
    : undefined;
  const rawMessageTexts = Array.isArray(rawMessages)
    ? body.messages.filter((message) =>
      message && typeof message === "object" && message.type === "text" &&
      typeof message.text === "string"
    ).map((message) => message.text)
    : [];
  const texts = legacyTexts ??
    (legacyText?.trim()
      ? [
        legacyText,
      ]
      : rawMessageTexts);
  const text = texts.join("\n\n");
  const legacyImages = body.images === undefined
    ? undefined
    : Array.isArray(body.images)
    ? body.images.filter((image) => image && typeof image === "object").map((
      image,
    ) => ({
      originalContentUrl: typeof image.originalContentUrl === "string"
        ? image.originalContentUrl
        : "",
      previewImageUrl: typeof image.previewImageUrl === "string"
        ? image.previewImageUrl
        : undefined,
    }))
    : [];
  const images = legacyImages ?? [];
  const deliveryModeParam = typeof body.delivery_mode === "string"
    ? body.delivery_mode
    : null;
  const isNoSend = deliveryModeParam === "no_send";

  let payload;
  if (isNoSend) {
    payload = await buildSuppressedOutboundPayload(
      recipient,
      body,
      text,
      texts,
      images,
    );
  } else {
    try {
      payload = buildLinePushPayload({
        to: recipient,
        messages: rawMessages,
        text: legacyText,
        texts: legacyTexts,
        images: legacyImages,
        quickReply: body.quickReply,
      });
    } catch (error) {
      return jsonResponse({
        ok: false,
        error: error instanceof Error
          ? error.message
          : "invalid_line_message_payload",
      }, 400);
    }
  }
  const outboundMessageType = inferLineMessageType(payload.messages);
  const accessToken = Deno.env.get(lineAccessTokenEnvForChannel(channel));
  if (!accessToken) {
    return jsonResponse({
      ok: false,
      error: "missing_line_channel_access_token",
    }, 500);
  }
  const supabase = createSupabaseClient();
  const correlationId = typeof body.correlation_id === "string"
    ? body.correlation_id
    : crypto.randomUUID();
  const conversationId = typeof body.conversation_id === "string"
    ? body.conversation_id
    : null;
  const sourceEventId = typeof body.source_event_id === "string"
    ? body.source_event_id
    : null;
  const idempotencyKey = typeof body.idempotency_key === "string" &&
      body.idempotency_key.trim().length > 0 &&
      body.idempotency_key.trim().length <= 200
    ? body.idempotency_key.trim()
    : null;
  const replyToken = typeof body.reply_token_ephemeral === "string"
    ? body.reply_token_ephemeral.trim()
    : "";
  let outbound = null;
  if (idempotencyKey) {
    const { data: existing, error: existingError } = await supabase
      .from("outbound_messages")
      .select("id,send_status,delivery_mode")
      .eq("target_channel", channel)
      .eq("recipient_ref", payload.to)
      .eq("idempotency_key", idempotencyKey)
      .maybeSingle();
    if (existingError) {
      return jsonResponse({ ok: false, error: existingError.message }, 500);
    }
    if (
      existing?.send_status === "sent" || existing?.send_status === "sending" ||
      existing?.send_status === "suppressed"
    ) {
      return jsonResponse({
        ok: true,
        replayed: true,
        outbound_message_id: existing.id,
        channel,
        delivery_mode: existing.delivery_mode,
        ...(existing?.send_status === "suppressed" ? { suppressed: true } : {}),
      }, 200);
    }
    if (existing) {
      const { data: retryRow, error: retryError } = await supabase
        .from("outbound_messages")
        .update({
          correlation_id: correlationId,
          source_event_id: sourceEventId,
          conversation_id: conversationId,
          payload,
          delivery_mode: isNoSend ? "no_send" : (replyToken ? "reply" : "push"),
          send_status: isNoSend ? "suppressed" : "sending",
          error: null,
          updated_at: new Date().toISOString(),
        })
        .eq("id", existing.id)
        .select("id")
        .single();
      if (retryError) {
        return jsonResponse({ ok: false, error: retryError.message }, 500);
      }
      outbound = retryRow;
    }
  }

  if (!outbound) {
    const { data: inserted, error: insertError } = await supabase.from(
      "outbound_messages",
    ).insert({
      correlation_id: correlationId,
      source_event_id: sourceEventId,
      conversation_id: conversationId,
      target_channel: channel,
      recipient_ref: payload.to,
      message_type: outboundMessageType,
      payload,
      delivery_mode: isNoSend ? "no_send" : (replyToken ? "reply" : "push"),
      send_status: isNoSend ? "suppressed" : "sending",
      approval_status: "not_required",
      idempotency_key: idempotencyKey,
    }).select("id").single();
    if (insertError) {
      return jsonResponse({
        ok: false,
        error: insertError.message,
      }, 500);
    }
    outbound = inserted;
  }

  if (outbound.send_status === "suppressed" || isNoSend) {
    return jsonResponse({
      ok: true,
      suppressed: true,
      outbound_message_id: outbound.id,
      delivery_mode: "no_send",
    }, 200);
  }

  let sendResult = replyToken
    ? await sendLineReply({
      accessToken,
      replyToken,
      to: payload.to,
      messages: payload.messages,
    })
    : await sendLinePush({
      accessToken,
      to: payload.to,
      messages: payload.messages,
    });
  let finalDeliveryMode = replyToken ? "reply" : "push";
  const replyError = !sendResult.ok && replyToken ? sendResult.error : null;
  if (!sendResult.ok && replyToken) {
    sendResult = await sendLinePush({
      accessToken,
      to: payload.to,
      messages: payload.messages,
    });
    finalDeliveryMode = "push";
  }
  if (!sendResult.ok) {
    await supabase.from("outbound_messages").update({
      send_status: "failed",
      error: replyError
        ? {
          reply: replyError,
          push: sendResult.error,
        }
        : sendResult.error,
      updated_at: new Date().toISOString(),
    }).eq("id", outbound.id);
    return jsonResponse({
      ok: false,
      outbound_message_id: outbound.id,
      delivery_mode: finalDeliveryMode,
      error: replyError
        ? {
          reply: replyError,
          push: sendResult.error,
        }
        : sendResult.error,
    }, 502);
  }
  const sentAt = new Date().toISOString();
  await supabase.from("outbound_messages").update({
    send_status: "sent",
    provider_response: {
      ...sendResult.providerResponse,
      delivery_mode: finalDeliveryMode,
      ...replyError
        ? {
          reply_fallback_error: replyError,
        }
        : {},
    },
    delivery_mode: finalDeliveryMode,
    sent_at: sentAt,
    updated_at: sentAt,
  }).eq("id", outbound.id);
  if (conversationId) {
    const { error: messageError } = await supabase.from("conversation_messages")
      .insert({
        conversation_id: conversationId,
        outbound_message_id: outbound.id,
        correlation_id: correlationId,
        sender_type: "bot",
        sender_ref: "line-send-endpoint",
        channel,
        message_type: outboundMessageType,
        body: text,
        payload,
        direction: "outbound",
        visibility: "guest_visible",
      });
    if (messageError) {
      return jsonResponse({
        ok: false,
        outbound_message_id: outbound.id,
        error: messageError.message,
      }, 500);
    }
  }
  return jsonResponse({
    ok: true,
    outbound_message_id: outbound.id,
    channel,
    delivery_mode: finalDeliveryMode,
    recipient_tail: `...${payload.to.slice(-6)}`,
  }, 200);
}
async function dispatchToN8n(job) {
  const n8nUrl = Deno.env.get("N8N_LINE_GATEWAY_INGEST_URL");
  if (!n8nUrl) {
    return {
      ok: false,
      error: "missing_n8n_line_gateway_ingest_url",
    };
  }
  try {
    const response = await fetch(n8nUrl, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-impact-webhook-secret": Deno.env.get("N8N_WEBHOOK_SECRET") ?? "",
      },
      body: JSON.stringify(job),
    });
    if (!response.ok) {
      return {
        ok: false,
        error: `n8n_dispatch_failed_${response.status}`,
      };
    }
    return {
      ok: true,
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "n8n_dispatch_failed",
    };
  }
}
async function markWebhookEventFailed(supabase, webhookEventId, message) {
  await supabase.from("line_webhook_events").update({
    processing_status: "failed",
    error: {
      message,
    },
    processed_at: new Date().toISOString(),
  }).eq("id", webhookEventId);
}
function createSupabaseClient() {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("IMPACT_SUPABASE_SECRET_KEY") ||
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
  }
  return createClient(supabaseUrl, serviceRoleKey, {
    auth: {
      persistSession: false,
    },
  });
}
function getLineChannelSecret(channel) {
  const envByChannel = {
    guest_oa: "LINE_GUEST_CHANNEL_SECRET",
    internal_ops_oa: "LINE_INTERNAL_OPS_CHANNEL_SECRET",
    housekeeping_line: "LINE_HOUSEKEEPING_CHANNEL_SECRET",
  };
  return Deno.env.get(envByChannel[channel]) ?? null;
}
function normalizeMessageType(type) {
  if (
    type === "text" || type === "image" || type === "video" ||
    type === "audio" || type === "file" || type === "location" ||
    type === "sticker"
  ) {
    return type;
  }
  return "other";
}
function parseLineChannel(value) {
  if (
    value === "guest_oa" || value === "internal_ops_oa" ||
    value === "housekeeping_line"
  ) {
    return value;
  }
  return null;
}
function jsonResponse(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...corsHeaders,
      "content-type": "application/json; charset=utf-8",
    },
  });
}
