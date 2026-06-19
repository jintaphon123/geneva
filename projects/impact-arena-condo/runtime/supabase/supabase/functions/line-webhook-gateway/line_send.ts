type LineImage = {
  originalContentUrl: string;
  previewImageUrl?: string;
};

type LineSendInput = {
  accessToken?: string;
  replyToken?: string;
  to: string;
  messages?: Record<string, unknown>[];
  text?: string;
  texts?: string[];
  images?: LineImage[];
  quickReply?: unknown;
};

const ALLOWED_LINE_MESSAGE_TYPES = new Set([
  "text",
  "image",
  "flex",
]);

function validateRawMessages(messages: unknown[]): Record<string, unknown>[] {
  if (messages.length < 1 || messages.length > 5) {
    throw new Error("line_message_payload_exceeds_limit");
  }
  return messages.map((message) => {
    if (!message || typeof message !== "object" || Array.isArray(message)) {
      throw new Error("invalid_line_message");
    }
    const type = (message as Record<string, unknown>).type;
    if (typeof type !== "string" || !ALLOWED_LINE_MESSAGE_TYPES.has(type)) {
      throw new Error("unsupported_line_message_type");
    }
    if (
      type === "flex" &&
      typeof (message as Record<string, unknown>).altText !== "string"
    ) {
      throw new Error("missing_flex_alt_text");
    }
    return message as Record<string, unknown>;
  });
}

export function inferLineMessageType(
  messages: Record<string, unknown>[],
): "text" | "image" | "flex" | "other" {
  if (messages.length === 0) {
    return "other";
  }
  const firstType = messages[0].type;
  if (
    typeof firstType === "string" &&
    ALLOWED_LINE_MESSAGE_TYPES.has(firstType) &&
    messages.every((message) => message.type === firstType)
  ) {
    return firstType as "text" | "image" | "flex";
  }
  return "other";
}

export function buildLineTextPushPayload(to: string, text: string) {
  return buildLinePushPayload({
    to,
    text,
  });
}
function buildLineMessages(
  input: Pick<
    LineSendInput,
    "messages" | "text" | "texts" | "images" | "quickReply"
  >,
) {
  if (input.messages !== undefined) {
    if (
      input.text !== undefined ||
      input.texts !== undefined ||
      input.images !== undefined ||
      input.quickReply !== undefined
    ) {
      throw new Error("mixed_line_message_payload");
    }
    if (!Array.isArray(input.messages)) {
      throw new Error("invalid_line_message");
    }
    return validateRawMessages(input.messages);
  }

  const messages = [];
  const textValues = Array.isArray(input.texts) ? input.texts : [
    input.text,
  ];
  const activeTexts = textValues.filter(
    (v): v is string => typeof v === "string" && v.trim() !== "",
  );

  for (let i = 0; i < activeTexts.length; i++) {
    const textValue = activeTexts[i];
    const msg: any = {
      type: "text",
      text: textValue.trim(),
    };
    if (i === activeTexts.length - 1 && input.quickReply) {
      msg.quickReply = input.quickReply;
    }
    messages.push(msg);
  }

  const images = input.images ?? [];
  for (let i = 0; i < images.length; i++) {
    const image = images[i];
    const originalContentUrl = image.originalContentUrl.trim();
    const previewImageUrl = (image.previewImageUrl ?? image.originalContentUrl)
      .trim();
    if (
      !originalContentUrl.startsWith("https://") ||
      !previewImageUrl.startsWith("https://")
    ) {
      throw new Error("invalid_line_image_url");
    }
    const msg: any = {
      type: "image",
      originalContentUrl,
      previewImageUrl,
    };
    if (
      activeTexts.length === 0 &&
      i === images.length - 1 &&
      input.quickReply
    ) {
      msg.quickReply = input.quickReply;
    }
    messages.push(msg);
  }

  if (messages.length === 0) {
    throw new Error("missing_line_message_payload");
  }
  if (messages.length > 5) {
    throw new Error("line_message_payload_exceeds_limit");
  }
  return messages;
}
export function buildLinePushPayload(input: LineSendInput) {
  const trimmedTo = input.to.trim();
  if (!trimmedTo) {
    throw new Error("missing_line_recipient");
  }
  return {
    to: trimmedTo,
    messages: buildLineMessages(input),
  };
}
export function buildLineReplyPayload(
  input: LineSendInput & { replyToken: string },
) {
  const replyToken = input.replyToken.trim();
  if (!replyToken) {
    throw new Error("missing_line_reply_token");
  }
  return {
    replyToken,
    messages: buildLineMessages(input),
  };
}
export function lineAccessTokenEnvForChannel(channel: string) {
  const envByChannel: Record<string, string> = {
    guest_oa: "LINE_GUEST_CHANNEL_ACCESS_TOKEN",
    internal_ops_oa: "LINE_INTERNAL_OPS_CHANNEL_ACCESS_TOKEN",
    housekeeping_line: "LINE_HOUSEKEEPING_CHANNEL_ACCESS_TOKEN",
  };
  return envByChannel[channel];
}
export function normalizeLineSendError(status: number, body: string) {
  const safeBody = body.slice(0, 500);
  let providerMessage = safeBody;
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed?.message === "string" && parsed.message.trim()) {
      providerMessage = parsed.message.trim();
    }
  } catch {
    // Keep the bounded raw provider response.
  }
  const code = status === 429 &&
      /(?:monthly\s+limit|reached\s+your\s+monthly\s+limit)/i.test(
        providerMessage,
      )
    ? "line_monthly_quota_exhausted"
    : "line_provider_error";
  return {
    status,
    code,
    message: providerMessage.slice(0, 300),
    body: safeBody,
  };
}
export async function sendLineTextPush(
  input: LineSendInput & { accessToken: string },
) {
  return await sendLinePush({
    accessToken: input.accessToken,
    to: input.to,
    text: input.text,
  });
}
export async function sendLinePush(
  input: LineSendInput & { accessToken: string },
) {
  const response = await fetch("https://api.line.me/v2/bot/message/push", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${input.accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(buildLinePushPayload(input)),
  });
  const responseText = await response.text();
  if (!response.ok) {
    return {
      ok: false,
      error: normalizeLineSendError(response.status, responseText),
    };
  }
  return {
    ok: true,
    providerResponse: responseText ? JSON.parse(responseText) : {},
  };
}
export async function sendLineReply(
  input: LineSendInput & { accessToken: string; replyToken: string },
) {
  const response = await fetch("https://api.line.me/v2/bot/message/reply", {
    method: "POST",
    headers: {
      "authorization": `Bearer ${input.accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(buildLineReplyPayload(input)),
  });
  const responseText = await response.text();
  if (!response.ok) {
    return {
      ok: false,
      error: normalizeLineSendError(response.status, responseText),
    };
  }
  return {
    ok: true,
    providerResponse: responseText ? JSON.parse(responseText) : {},
  };
}
