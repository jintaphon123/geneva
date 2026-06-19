import {
  assertEquals,
  assertThrows,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import {
  buildLinePushPayload,
  buildLineReplyPayload,
  inferLineMessageType,
  normalizeLineSendError,
} from "./line_send.ts";

Deno.test("buildLinePushPayload preserves multiple text bubbles before images", () => {
  const payload = buildLinePushPayload({
    to: "U123456789",
    texts: [
      "ยืนยันข้อมูลเรียบร้อยแล้วนะคะ",
      "คุณมาลี เดินทางมายังไงหรอคะ",
    ],
    images: [
      {
        originalContentUrl: "https://example.com/original.jpg",
        previewImageUrl: "https://example.com/preview.jpg",
      },
    ],
  });

  assertEquals(payload.messages, [
    { type: "text", text: "ยืนยันข้อมูลเรียบร้อยแล้วนะคะ" },
    { type: "text", text: "คุณมาลี เดินทางมายังไงหรอคะ" },
    {
      type: "image",
      originalContentUrl: "https://example.com/original.jpg",
      previewImageUrl: "https://example.com/preview.jpg",
    },
  ]);
});

Deno.test("normalizeLineSendError identifies exhausted monthly quota without truncating the provider message", () => {
  const error = normalizeLineSendError(
    429,
    JSON.stringify({ message: "You have reached your monthly limit." }),
  );

  assertEquals(error, {
    status: 429,
    code: "line_monthly_quota_exhausted",
    message: "You have reached your monthly limit.",
    body: JSON.stringify({ message: "You have reached your monthly limit." }),
  });
});

Deno.test("buildLinePushPayload preserves a raw Flex message exactly", () => {
  const flex = {
    type: "flex",
    altText: "คิวงานแม่บ้าน 5 งาน",
    contents: { type: "carousel", contents: [] },
  };

  assertEquals(buildLinePushPayload({ to: " U1 ", messages: [flex] }), {
    to: "U1",
    messages: [flex],
  });
});

Deno.test("raw LINE messages are bounded and use supported message types", () => {
  const sixMessages = Array.from(
    { length: 6 },
    (_, index) => ({ type: "text", text: `message-${index}` }),
  );
  assertThrows(
    () => buildLinePushPayload({ to: "U1", messages: sixMessages }),
    Error,
    "line_message_payload_exceeds_limit",
  );
  assertThrows(
    () =>
      buildLinePushPayload({
        to: "U1",
        messages: [{
          type: "flex",
          contents: { type: "bubble" },
        }],
      }),
    Error,
    "missing_flex_alt_text",
  );
  assertThrows(
    () =>
      buildLinePushPayload({
        to: "U1",
        messages: [{ type: "sticker", packageId: "1", stickerId: "1" }],
      }),
    Error,
    "unsupported_line_message_type",
  );
});

Deno.test("raw LINE messages cannot be mixed with legacy message fields", () => {
  const messages = [{ type: "text", text: "raw" }];

  for (
    const legacyFields of [
      { text: "legacy" },
      { texts: ["legacy"] },
      {
        images: [{
          originalContentUrl: "https://example.com/image.jpg",
        }],
      },
      { quickReply: { items: [] } },
    ]
  ) {
    assertThrows(
      () => buildLinePushPayload({ to: "U1", messages, ...legacyFields }),
      Error,
      "mixed_line_message_payload",
    );
  }
});

Deno.test("raw push and reply payloads require their delivery identifiers", () => {
  const messages = [{ type: "text", text: "raw" }];

  assertThrows(
    () => buildLinePushPayload({ to: " ", messages }),
    Error,
    "missing_line_recipient",
  );
  assertThrows(
    () =>
      buildLineReplyPayload({
        to: "U1",
        replyToken: " ",
        messages,
      }),
    Error,
    "missing_line_reply_token",
  );
});

Deno.test("inferLineMessageType uses the final bounded message payload", () => {
  assertEquals(
    inferLineMessageType([{
      type: "flex",
      altText: "คิวงาน",
      contents: { type: "bubble" },
    }]),
    "flex",
  );
  assertEquals(
    inferLineMessageType([
      { type: "text", text: "หนึ่ง" },
      {
        type: "image",
        originalContentUrl: "https://example.com/image.jpg",
        previewImageUrl: "https://example.com/image.jpg",
      },
    ]),
    "other",
  );
});
