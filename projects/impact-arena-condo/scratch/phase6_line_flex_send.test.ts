import {
  assertEquals,
  assertMatch,
  assertThrows,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import {
  buildLinePushPayload,
  buildLineReplyPayload,
} from "../runtime/supabase/supabase/functions/line-webhook-gateway/line_send.ts";

const flex = {
  type: "flex",
  altText: "รายละเอียดงานห้อง T-01",
  contents: {
    type: "bubble",
    body: {
      type: "box",
      layout: "vertical",
      contents: [{ type: "text", text: "T-01" }],
    },
  },
};

Deno.test("Phase 6 Flex transport preserves the exact push payload", () => {
  assertEquals(
    buildLinePushPayload({
      to: "Uhousekeeper",
      messages: [flex],
    }),
    {
      to: "Uhousekeeper",
      messages: [flex],
    },
  );
});

Deno.test("Phase 6 Flex transport preserves the exact reply payload", () => {
  assertEquals(
    buildLineReplyPayload({
      to: "Uhousekeeper",
      replyToken: "reply-token",
      messages: [flex],
    }),
    {
      replyToken: "reply-token",
      messages: [flex],
    },
  );
});

Deno.test("Phase 6 Flex transport rejects empty and primitive raw messages", () => {
  assertThrows(
    () => buildLinePushPayload({ to: "Uhousekeeper", messages: [] }),
    Error,
    "line_message_payload_exceeds_limit",
  );
  assertThrows(
    () =>
      buildLinePushPayload({
        to: "Uhousekeeper",
        messages: ["not-a-line-message" as unknown as Record<string, unknown>],
      }),
    Error,
    "invalid_line_message",
  );
});

Deno.test("Phase 6 gateway keeps raw messages on build, send, and persistence paths", async () => {
  const gatewaySource = await Deno.readTextFile(
    new URL(
      "../runtime/supabase/supabase/functions/line-webhook-gateway/index.ts",
      import.meta.url,
    ),
  );

  assertMatch(
    gatewaySource,
    /const rawMessages = body\.messages === undefined\s*\?\s*undefined\s*:\s*body\.messages;/,
  );
  assertMatch(
    gatewaySource,
    /const legacyImages = body\.images === undefined[\s\S]*?const images = legacyImages \?\? \[\];/,
  );
  assertMatch(
    gatewaySource,
    /buildLinePushPayload\(\{[\s\S]*?messages: rawMessages,[\s\S]*?images: legacyImages,[\s\S]*?\}\)/,
  );
  assertMatch(
    gatewaySource,
    /sendLineReply\(\{[\s\S]*?messages: payload\.messages,[\s\S]*?\}\)/,
  );
  assertMatch(
    gatewaySource,
    /sendLinePush\(\{[\s\S]*?messages: payload\.messages,[\s\S]*?\}\)/,
  );
  assertMatch(
    gatewaySource,
    /message_type: outboundMessageType,[\s\S]*?payload,/,
  );
});
