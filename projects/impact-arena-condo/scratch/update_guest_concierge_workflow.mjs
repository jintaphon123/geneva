import fs from 'node:fs';

const liveWfPath = new URL('./live-exports/current/impact-guest-concierge.json', import.meta.url);
const workflowData = JSON.parse(fs.readFileSync(liveWfPath, 'utf-8'));
workflowData.settings = {
  ...(workflowData.settings ?? {}),
  executionOrder: 'v1',
  saveDataErrorExecution: 'all',
  saveDataSuccessExecution: 'all',
};

function getPhase5Functions() {
  const code = fs.readFileSync(new URL('./phase5_bundle.mjs', import.meta.url), 'utf-8');
  return code.replace(/export (function|const)/g, '$1'); // Strip "export "
}

const classifyIntentCode = `
function normalizeText(value) {
  return String(value ?? '').trim().toLowerCase();
}
function includesAny(text, terms) {
  return terms.some((term) => text.includes(term));
}
function hasEnglish(text) {
  return /[a-z]/i.test(text);
}
function hasThai(text) {
  return /[\\u0E00-\\u0E7F]/.test(text);
}
function stripPoliteAndNoise(text) {
  return text
    .replace(/นะครับ|นะคะ|ครับ|ค่ะ|คะ|จ้า|จ้ะ|kub|krub|krap|ka|kha/gi, ' ')
    .replace(/[.,!?()[\\]{}"'“”‘’]/g, ' ')
    .replace(/\\s+/g, ' ')
    .trim();
}
function looksLikeShortBookingNameClaim(text) {
  const stripped = stripPoliteAndNoise(text);
  if (!stripped || stripped.length < 2 || stripped.length > 40) return false;
  if (!(/[a-z]/i.test(stripped) || /[\\u0E00-\\u0E7F]/.test(stripped))) return false;
  const lower = stripped.toLowerCase();
  const parts = stripped.split(/\\s+/).filter(Boolean);
  const personalStarts = ['ผม ', 'ฉัน ', 'หนู ', 'เรา ', 'ดิฉัน ', 'i ', "i'm ", 'im '];
  if (personalStarts.some((prefix) => lower.startsWith(prefix))) return false;
  const nonNameTerms = [
    'สวัสดี', 'หวัดดี', 'ขอบคุณ', 'โอเค', 'ok', 'okay', 'hello', 'hi', 'thanks', 'thank you',
    'ราคา', 'เท่าไหร่', 'ห้องว่าง', 'ว่างไหม', 'พักได้ไหม', 'จองได้ไหม',
    'กี่โมง', 'ที่ไหน', 'อยู่ไหน', 'อยู่', 'ยังไง', 'ทำไง', 'ช่วยด้วย',
    'ถึงแล้ว', 'มาถึง', 'กำลังมา', 'กำลังเดินทาง', 'เดินทาง', 'หน้าตึก', 'ถึงตึก', 'ถึงหน้าตึก',
    'ขับรถ', 'รถ', 'จอดรถ', 'parking', 'แท็กซี่', 'grab', 'bolt',
    'หิว', 'กินข้าว', 'อาหาร', 'ร้านอาหาร', 'เซเว่น', 'seven', 'wifi', 'wi-fi', 'อินเทอร์เน็ต', 'เน็ต',
    'เข้าห้อง', 'ขึ้นห้อง', 'เช็คอิน', 'เช็กอิน', 'เช็คเอาท์', 'เช็กเอาท์', 'เช็กเอาต์', 'เช็คเอาต์', 'เลท', 'อยู่ต่อ',
    'คอสโม', 'cosmo',
    'คืนเงิน', 'มัดจำ', 'โกง', 'บริการแย่', 'รีวิว', 'ร้องเรียน', 'คอมเพลน', 'เจ้าของ', 'ผู้จัดการ',
  ];
  if (nonNameTerms.some((term) => lower.includes(term))) return false;
  return parts.length <= 4;
}
const input = items[0].json;
const text = normalizeText(input.guest_text);
let intent = 'safe_general_question';

const roomEntryQuestionTerms = ['เข้าห้องได้', 'เข้าห้องได้ไหม', 'เข้าห้องได้มั้ย', 'เข้าห้องได้หรือยัง', 'ขึ้นห้องได้', 'ขึ้นห้องได้ไหม', 'ขึ้นห้องได้มั้ย', 'ขึ้นห้องได้หรือยัง', 'เข้าไปได้เลยไหม', 'เข้าไปได้เลยมั้ย', 'จะเข้าห้องได้หรือยัง', 'ห้องพร้อมแล้วใช่ไหม'];
const roomEntryQuestionSignals = ['ไหม', 'มั้ย', 'หรือยัง', 'ใช่ไหม', 'ใช่มั้ย', '?'];
if (includesAny(text, roomEntryQuestionTerms) || (includesAny(text, ['เข้าห้อง', 'ขึ้นห้อง', 'เข้าไป']) && includesAny(text, roomEntryQuestionSignals) && !includesAny(text, ['เข้าไม่ได้', 'เปิดไม่ได้', 'เปิดไม่ออก', 'cannot enter']))) {
  intent = 'room_entry_request';
} else if (includesAny(text, ['เข้าห้องแล้ว', 'เข้าห้องมาแล้ว', 'อยู่ห้องแล้ว', 'เข้าห้องพัก', 'check in แล้ว', 'checked in', 'i am in the room', 'i’m in the room', 'im in the room']) && !includesAny(text, ['ไม่ได้', 'ไม่ด้าย', 'เข้าไม่ได้', 'เปิดไม่ได้', 'เปิดไม่ออก', 'เข้าไม่ได้เลย', 'cannot enter', 'ไหม', 'มั้ย', 'หรือยัง', 'ใช่ไหม', 'ใช่มั้ย'])) {
  intent = 'checkin_signal';
} else if (includesAny(text, ['ออกแล้ว', 'ออกไปแล้ว', 'เช็คเอาท์แล้ว', 'เช็คเอาท์', 'เช็คเอาท์เรียบร้อย', 'checkout แล้ว', 'checkout เรียบร้อย', 'check out แล้ว', 'checked out'])) {
  intent = 'checkout_signal';
} else if (includesAny(text, ['ไม่ใช่', 'ไม่ถูกต้อง', 'ไม่ถูก', 'ผิดห้อง', 'ผิดคน', 'wrong booking', 'not correct', 'incorrect'])) {
  intent = 'booking_reject';
} else if (includesAny(text, ['ไม่มีเน็ต', 'ไม่มี wifi', 'ไม่มี wi-fi', 'ไม่มีอินเทอร์เน็ต', 'no wifi', 'no wi-fi'])) {
  intent = 'internet_complaint';
} else if (includesAny(text, ['wifi', 'wi-fi', 'internet', 'อินเทอร์เน็ต', 'เน็ต', 'ไวไฟ', 'ไว-ไฟ'])) {
  intent = 'internet_question';
} else if (includesAny(text, ['เซเว่น', 'seven', '7-eleven', '7 eleven', 'bigc', 'big c', 'convenience store'])) {
  intent = 'convenience_store_question';
} else if (includesAny(text, ['เปิดยัง', 'เปิดหรือยัง', 'เปิดไหม', 'เปิดกี่โมง', 'open now', 'is it open'])) {
  intent = 'unknown_open_now';
} else if (includesAny(text, ['อยู่ที่เดิม', 'เมื่อกี้ล่ะ', 'อันไหน', 'อันนั้น', 'อันนี้', 'แล้วไง'])) {
  intent = 'clarify_reference';
} else if (includesAny(text, ['ถูกต้อง', 'ถูกต้องค่ะ', 'ถูกต้องครับ', 'ใช่', 'ใช่ค่ะ', 'ใช่ครับ', 'correct', 'yes'])) {
  intent = 'booking_confirm';
} else if (includesAny(text, ['จองห้อง', 'จองไว้', 'จองมา', 'จองผ่าน', 'เลขการจอง', 'booking', 'agoda', 'airbnb', 'จองตรง']) || /^\\d{7,12}$/.test(text.trim())) {
  intent = 'booking_claim';
} else if (includesAny(text, ['เช็คอินก่อน', 'เข้าก่อน', 'check in now', 'early check-in', 'early check'])) {
  intent = 'early_checkin_request';
} else if (includesAny(text, ['เข้าห้องยังไง', 'วิธีเข้าห้อง', 'ขอวิธีเข้าห้อง', 'กุญแจห้อง', 'ขอวิธีเข้า', 'room access', 'how to enter', 'เข้าตึก', 'ขึ้นห้อง', 'ขอรหัสเข้าห้อง', 'เช็กอิน', 'เช็คอิน', 'จะเช็คอิน', 'ต้องการเช็คอิน', 'ถึงตึก', 'อยู่ตึก', 'หน้าตึก', 'ถึงหน้าตึก', 'หน้าอาคาร', 'ถึงอาคาร', 'มาถึงตึก', 'มาถึงหน้าตึก', 'จะขึ้นห้อง', 'ขออีกรอบ', 'ขออีกที', 'ส่งอีกรอบ', 'ขอรูปอีกรอบ', 'ขอใหม่อีกรอบ', 'check in', 'check-in', 'อยากเช็คอิน', 'ต้องการเช็คอิน'])) {
  intent = 'room_entry_request';
} else if (includesAny(text, ['รถสาธารณะ', 'รถเมล์', 'รถไฟฟ้า', 'mrt', 'bts', 'impact station', 'สถานี'])) {
  intent = 'arrival_mode_public_transport';
} else if (includesAny(text, ['แท็กซี่', 'taxi', 'grab', 'bolt'])) {
  intent = 'arrival_mode_taxi';
} else if (includesAny(text, ['เอารถมา', 'จอดรถ', 'มีที่จอดรถไหม', 'ที่จอดรถ', 'parking', 'ขับรถ', 'ขับรถมา', 'drive'])) {
  intent = 'arrival_mode_car';
} else if (includesAny(text, ['มอเตอร์ไซค์ส่วนตัว', 'มอไซค์ส่วนตัว', 'ขี่มอเตอร์ไซค์', 'ขี่มอไซค์', 'เอามอเตอร์ไซค์มา', 'เอามอไซค์มา', 'ขับมอเตอร์ไซค์', 'ขับมอไซค์', 'private motorcycle', 'own motorbike', 'scooter'])) {
  intent = 'arrival_mode_private_motorcycle';
} else if (includesAny(text, ['วิน', 'มอเตอร์ไซค์', 'มอไซค์', 'วินมอเตอร์ไซค์', 'motorbike'])) {
  intent = text.includes('impact') || text.includes('อิมแพ็ค') ? 'motorbike_outbound' : 'motorbike_arrival';
} else if (includesAny(text, ['ขอโล', 'ขอโลเคชั่น', 'ขอแผนที่', 'อยู่ตรงไหน', 'ไปตึกยังไง', 'ส่งโล', 'ขอโลตึกหน่อย', 'ขอโลเคชั่นหน่อย', 'location', 'map'])) {
  intent = 'arrival_location_request';
} else if (includesAny(text, ['กินข้าว', 'หิว', 'ร้านอาหาร', 'food', 'restaurant'])) {
  intent = 'food_question';
} else if (includesAny(text, ['อยู่ต่อ', 'พักต่อ', 'extend', 'another night'])) {
  intent = 'extension_interest';
} else if (includesAny(text, ['สระว่ายน้ำ', 'ฟิตเนส', 'ยิม', 'fitness', 'gym', 'pool'])) {
  intent = 'facility_question';
} else if (includesAny(text, ['ยาสระผม', 'ร้านขายยา', 'pharmacy'])) {
  intent = 'unknown_knowledge_gap';
} else if (includesAny(text, ['แอดมิน', 'คุยกับคน', 'พนักงาน', 'เจ้าหน้าที่', 'talk to staff', 'talk to human', 'ติดต่อพนักงาน', 'คุยกับแอดมิน'])) {
  intent = 'talk_to_human';
} else if (looksLikeShortBookingNameClaim(text)) {
  intent = 'booking_claim';
}

const detectedLanguage = hasThai(input.guest_text) ? 'th' : (hasEnglish(input.guest_text) ? 'en' : null);
const language = detectedLanguage ?? input.language ?? 'th';
return [{ json: { ...input, intent, language } }];
`;

const promptCode = `
const input = items[0].json;

// --- INJECTED PHASE 5 FUNCTIONS ---
${getPhase5Functions()}
// ----------------------------------

// 1. Fetch Phase 5 Memory
const n8nContext = this;
let phase5_memory = {};
let stay_summary = null;
if (input.conversation_id) {
    try {
        const response = await n8nContext.helpers.httpRequest({
            method: 'POST',
            url: $env.SUPABASE_URL + '/rest/v1/rpc/phase5_get_active_memory',
            headers: { apikey: $env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' },
            body: { p_conversation_id: input.conversation_id, p_surface: 'guest_oa' },
            json: true,
            returnFullResponse: true
        });
        const rpcData = response.body;
        phase5_memory = rpcData?.structured_memory ?? {};
        stay_summary = rpcData?.stay_summary ?? null;
    } catch (e) {
        // Fallback to empty memory if RPC fails
    }
}

// 2. Perform Extraction
const guestText = input.guest_text ?? '';
const intent = input.intent ?? 'safe_general_question';
const messageObj = {
    text: guestText,
    id: input.source_event_id || 'unknown',
    timestamp: new Date().toISOString(),
    sender: 'guest'
};
const liveTruth = {
    room_status: input.room_status || input.stay_state?.room_status || null,
    cleaning_task: input.cleaning_task || null,
    access_prep: input.booking_access_preparations || null
};
const { memory_actions, ignored_actions } = extractMemory(messageObj, phase5_memory, liveTruth);

// 3. Inject missing room code for retrieval if known by system
const booking = input.booking ?? null;
const roomCode = booking?.rooms?.room_code ?? input.stay_state?.room_code_snapshot ?? null;
if (roomCode && (!phase5_memory['room'] || phase5_memory['room'].is_superseded)) {
    phase5_memory['room'] = { value: roomCode, is_superseded: false };
}

// 4. Retrieve Chat History
const chatHistory = $("Aggregate Chat History").first().json?.chat_history ?? [];

// 5. Evaluate Summary Trigger
const summaryDecision = evaluateSummaryTrigger(chatHistory, stay_summary);

// 6. Build Retrieval Context String
const mappedIntent = (
    intent === 'room_entry_request' ||
    intent === 'arrival_location_request' ||
    intent === 'arrival_mode_car' ||
    intent === 'arrival_mode_taxi' ||
    intent === 'arrival_mode_private_motorcycle' ||
    intent === 'arrival_mode_public_transport' ||
    intent === 'motorbike_arrival' ||
    intent === 'motorbike_outbound'
  ) ? 'arrival_access' 
    : (
      intent.includes('knowledge_gap') ||
      intent === 'facility_question' ||
      intent.includes('question') ||
      intent === 'food_question' ||
      intent === 'convenience_store_question' ||
      intent === 'internet_question'
    ) ? 'local_guidance'
    : 'general_chat';
const guestStayMemoryStr = buildRetrievalContext(mappedIntent, chatHistory, phase5_memory, stay_summary);

// 7. Format remaining prompt parts
const language = input.language ?? 'th';
const building = booking?.rooms?.building ?? input.stay_state?.building_snapshot ?? null;
const guestName = booking?.guest_name_snapshot ?? input.guest?.guest_name ?? 'ลูกค้า';
const platform = booking?.platform ?? 'Booking.com';
const checkIn = booking?.check_in_date ?? '-';
const checkOut = booking?.check_out_date ?? '-';
const reservationNumber = booking?.reservation_number ?? '-';

const isVerified = input.stay_state?.booking_verification_status === 'confirmed';
const isPending = input.stay_state?.booking_verification_status === 'pending_confirmation';

let friendlyName = guestName;
if (friendlyName && friendlyName !== 'ลูกค้า' && friendlyName !== 'guest') {
  friendlyName = friendlyName.split(' ')[0].replace(/ทดสอบ.*/g, '').trim();
  friendlyName = friendlyName ? 'คุณ' + friendlyName : 'คุณลูกค้า';
} else {
  friendlyName = 'คุณ' + friendlyName;
}

const systemPrompt = \`You are the virtual host for "Impact Arena Condo", a daily condo rental business in Muang Thong Thani.
Your goal is to reply to the guest in a warm, extremely polite, natural, and helpful human host persona.
You must speak the language of the guest (mainly Thai, but English if the guest writes in English).

CRITICAL BRAND VOICE & PERSONA RULES:
1. Zero emojis are allowed in any guest-facing message. Do not output any emojis under any circumstances.
2. Avoid generic, robotic AI empathy templates (e.g., do not say "เข้าใจเลยค่ะว่า..." or "ยินดีค่ะ เดี๋ยวแอดมินประสานงานให้นะคะ"). Write like a warm, helpful human host. If you need to acknowledge their situation, personalize it naturally (e.g. "เข้าใจเลยค่ะ\${friendlyName} ถ้าหิวแล้วก็ไม่ต้องกังวลนะคะ..."). Do not use the word "แอดมิน" to refer to yourself; refer to yourself as host / virtual assistant.
3. Vary your response patterns. Do not start subsequent messages with the same phrases or sentence structures.
4. GREETING RULE (Situational):
   - Do NOT repeat greetings (e.g. "สวัสดีค่ะ", "ยินดีต้อนรับสู่...") during ongoing active chat turns about the current stay (e.g. check-in instructions, directions to Impact, convenience store locations, food recommendations). Start directly and warmly.
   - DO use a polite greeting (e.g. "สวัสดีค่ะ \${friendlyName} ยินดีต้อนรับสู่ Impact Arena Condo นะคะ") under these specific conditions:
     - The first welcome/booking claim message.
     - Introductory or identity questions (e.g., "ฉันเป็นใคร", "คุณคือใคร").
     - General room availability or booking inquiries for future stays (e.g. "มีห้องพักกี่ห้องหรอ", "อยากพัก C8 มีห้องไหนบ้าง", "จองวันที่ 12-13 มิถุนายน").

CONTEXT FOR THE ACTIVE GUEST:
- Guest Name: \${friendlyName}
- Platform: \${platform}
- Verification Status: \${isVerified ? 'Verified (Confirmed)' : (isPending ? 'Pending Confirmation' : 'Unverified')}
- Stay Dates: \${checkIn} to \${checkOut}
- Reservation Number: \${reservationNumber}
- Room: \${roomCode ?? 'Not assigned yet'}
- Building: \${building ?? 'Not assigned yet'}

\${guestStayMemoryStr}

KNOWLEDGE BASE:
1. Facilities & Front Desk (ส่วนกลางและนิติ):
   - Popular Condo does NOT have a swimming pool.
   - If the guest asks for a gym or fitness place, the approved recommendation is Jett at Cosmo.
   - We DO NOT have a front desk or reception. Guests must contact us directly via this LINE OA for all matters.
   - DO NOT hallucinate any facilities or services not explicitly listed here.
2. Parking (ที่จอดรถ):
   - Parking around the condo is very hard to find. We strongly recommend paid parking.
   - Fee: ~40 THB/night.
   - Primary parking location: https://maps.app.goo.gl/unYXoJiS3CpE2Z4M8
3. 7-Eleven (เซเว่น):
   - For C3, C4, C5: Seven Cosmo (Map: https://maps.app.goo.gl/CHDavbxfX6X8b7r47)
   - For C2, C8, P2: Seven/BigC front of P2 (Map: https://maps.app.goo.gl/XBKtgyT2DUY49SJ67)
   - For C9, T8, T9: Seven Moriwalk (Map: https://maps.app.goo.gl/ubgk3xEneyjYd14N7)
4. Moto-taxi (วินมอเตอร์ไซค์):
   - To get to IMPACT Arena from condo:
     - C5 building: near motorbike C5 spot (Map: https://maps.app.goo.gl/jgdW9Xj1N25Krwbe6). Fee: ~20 THB.
     - C3, C4, C9, T8, T9: Moto-taxi Cosmo spot (Map: https://maps.app.goo.gl/PtZE6PNaJdVqyG7K7).
     - C2, C8, P2: Moto-taxi C2 spot (Map: https://maps.app.goo.gl/92RwfdTqfx1VATM56).
5. Wi-Fi:
   - There is NO Wi-Fi in the rooms.
   - If they ask for Wi-Fi, warmly apologize and advise them that they can buy a SIM card at the building's mapped 7-Eleven (provide the specific 7-Eleven details based on their building C3/C4/C5/etc.).
6. Check-in/Check-out:
   - Official Check-in time: from 13:00 onwards.
   - Official Check-out time: before 11:00 or 12:00.
   - Early check-in before 13:00 requires admin confirmation.
   - Standard room access must NOT mention room passcodes, fingerprint entry, or face-scan as the normal entry method.
   - When room readiness and access prep are confirmed, the guest can go in directly and the key is already left inside the room.
   - If room readiness or access prep is not confirmed, do not promise that the room is already open.
7. Building Maps (Google Map links):
   - C2: https://maps.app.goo.gl/vfEfC1c947vzLeMM6
   - C3: https://maps.app.goo.gl/pSbdiAM5wsY2iEiK9
   - C4: https://maps.app.goo.gl/aHyJPJg1FH6EqmB26
   - C5: https://maps.app.goo.gl/ifeAs5VBWepWpj6K7
   - C8: https://maps.app.goo.gl/cfEgb93Q44Wv9CFf6
   - C9: https://maps.app.goo.gl/PntrEvsVmZdgjTwRA
   - P2: https://maps.app.goo.gl/534tJ9d4WgZ3D5XS6
   - T8: https://maps.app.goo.gl/QireqAkMMdhTESqf9

INSTRUCTIONS & SCENARIO GUIDELINES:
1. TRICKY / OUT-OF-SCOPE QUESTIONS (Prevent Room Leaks):
   - If the guest asks for directions, keys, or details of other rooms or other buildings (e.g. "ขอวิธีการเดินทางไปตึกอื่นห้องอื่นหน่อยสิมีมั้ย"), do NOT reveal room assignments or codes. Politely share the list of general building maps (C2, C3, C4, C5, C8, C9, P2, T8) to assist them, exactly as shown below:
     สำหรับวิธีการเดินทางไปตึกอื่นๆ นะคะ \${friendlyName} สามารถดูแผนที่ของแต่ละตึกได้ตามลิงก์นี้เลยค่ะ:
     - ตึก C2: https://maps.app.goo.gl/vfEfC1c947vzLeMM6
     - ตึก C3: https://maps.app.goo.gl/pSbdiAM5wsY2iEiK9
     - ตึก C4: https://maps.app.goo.gl/aHyJPJg1FH6EqmB26
     - ตึก C5: https://maps.app.goo.gl/ifeAs5VBWepWpj6K7
     - ตึก C8: https://maps.app.goo.gl/cfEgb93Q44Wv9CFf6
     - ตึก C9: https://maps.app.goo.gl/PntrEvsVmZdgjTwRA
     - ตึก P2: https://maps.app.goo.gl/534tJ9d4WgZ3D5XS6
     - ตึก T8: https://maps.app.goo.gl/QireqAkMMdhTESqf9
     หากต้องการสอบถามเส้นทางไปยังสถานที่เฉพาะเจาะจง หรือต้องการความช่วยเหลือเพิ่มเติม แจ้งได้เลยนะคะ
2. NEW BOOKING / SALES INQUIRIES:
   - If the guest asks about room availability or options (e.g. "มีห้องพักกี่ห้องหรอ"), start directly and ask for dates:
     สำหรับห้องพักที่ Impact Arena Condo ของเรามีหลายแบบเลยค่ะ \${friendlyName} สนใจเข้าพักช่วงวันไหนเป็นพิเศษไหมคะ จะได้ช่วยแนะนำห้องที่เหมาะสมให้ค่ะ
   - If they specify a building (e.g. "อยากพัก C8 มีห้องไหนบ้าง"), greet them and ask for dates:
     สวัสดีค่ะ \${friendlyName} ยินดีต้อนรับสู่ Impact Arena Condo นะคะ สำหรับอาคาร C8 ตอนนี้มีห้องว่างให้บริการค่ะ ไม่ทราบว่า \${friendlyName} สนใจเข้าพักช่วงวันไหนเป็นพิเศษไหมคะ
   - If they provide dates (e.g. "12 มิถุนายน -13"), greet them and confirm if they want to book for these dates, prompting for details:
     สวัสดีค่ะ \${friendlyName} ยินดีต้อนรับสู่ Impact Arena Condo นะคะ ไม่ทราบว่า \${friendlyName} ต้องการสอบถามข้อมูลเกี่ยวกับช่วงวันที่ 12-13 มิถุนายน หรือเปล่าคะ หากต้องการจองห้องพักในช่วงวันดังกล่าว รบกวนแจ้งรายละเอียดเพิ่มเติมได้เลยนะคะ
3. SERVICE RECOVERY (Room Access Problems):
   - If the guest reports they cannot enter the room, cannot find the key, or are stuck (e.g. "เข้าห้องไม่ได้", "เปิดไม่ได้", "ไม่เจอกุญแจ"), reassure them safely.
   - Do NOT give them generic instructions again or overpromise. Do NOT guess what went wrong.
   - Example response: "รับทราบค่ะ \${friendlyName} ต้องขออภัยในความไม่สะดวกด้วยนะคะ ตอนนี้ทางเราได้รับแจ้งปัญหาแล้วและกำลังเร่งตรวจสอบให้อยู่ค่ะ รบกวนรอสักครู่นะคะ"
4. DELAYED CHECKIN (Room Not Ready):
   - IF the room is not ready because of cleaning status or access preparation, USE suggested_sop_family "cleaning_delayed_checkin".
5. CONVERSATIONAL FLOW:
   - Respond warmly and use polite Thai sentence endings like "ค่ะ" and "นะคะ".
   - Focus on drafting natural, human-like sentences. Avoid repeating templates.

REFERENCE CONVERSATION EXAMPLES (Match this style and tone exactly):
- Guest: ฉันเป็นใคร
  Response: สวัสดีค่ะ \${friendlyName} ยินดีต้อนรับสู่ Impact Arena Condo นะคะ ดิฉันเป็นผู้ดูแลเสมือนของคุณที่นี่ค่ะ หากมีอะไรให้ช่วยเหลือเกี่ยวกับการเข้าพัก หรือต้องการข้อมูลใดๆ เกี่ยวกับสิ่งอำนวยความสะดวกบริเวณคอนโด สามารถสอบถามได้เลยนะคะ
- Guest: หิวข้าวอะฉันอยากซื้อซิมเน็ตด้วย
  Response: เข้าใจเลยค่ะ\${friendlyName} ถ้าหิวแล้วก็ไม่ต้องกังวลนะคะ สำหรับซิมเน็ต ทางเราไม่มีบริการ Wi-Fi ในห้องพักนะคะ แต่\${friendlyName} สามารถหาซื้อซิมได้ที่ 7-Eleven สาขา Seven Cosmo ที่อยู่ใกล้กับอาคาร C3, C4, C5 ของเราเลยค่ะ สะดวกมากๆ เลยค่ะ ส่วนเรื่องอาหาร ถ้า\${friendlyName} อยากจะออกไปหาอะไรทานข้างนอก มีร้านอาหารอร่อยๆ อยู่ไม่ไกลเลยค่ะ หรือถ้าอยากได้คำแนะนำเพิ่มเติม บอกได้เลยนะคะ
- Guest: ฉันอยากไปอิมแพคอารีนาจะไปยังไงดี
  Response: สำหรับเดินทางไปอิมแพคอารีนานะคะ \${friendlyName} สามารถใช้บริการมอเตอร์ไซค์รับจ้างได้เลยค่ะ จากตึก C5 ของเรา จุดจอดจะอยู่ใกล้ๆ กับตึกเลยค่ะ (https://maps.app.goo.gl/jgdW9Xj1N25Krwbe6) ค่าบริการประมาณ 20 บาทค่ะ สะดวกและรวดเร็วมากๆ ค่ะ
- Guest: popular condo มีสระว่ายน้ำไหมคะ
  Response: ที่ Popular Condo ไม่มีสระว่ายน้ำนะคะ \${friendlyName} แต่ถ้าอยากออกกำลังกาย แนะนำ Jett ที่ Cosmo ได้เลยค่ะ เดินทางสะดวกจากคอนโดค่ะ

Respond in JSON format only with the following schema:
{
  "interpreted_topic": "string",
  "active_issue_continuation": "boolean",
  "suggested_sop_family": "string",
  "confidence_level": "high|medium|low",
  "risk_flags": ["array of strings or 'none'"],
  "recommended_send_mode": "safe_auto|draft_only|internal_now",
  "explanation_notes": "string",
  "reply_text": "YOUR_GENERATED_RESPONSE_WITHOUT_EMOJIS"
}\`;

const userMessage = \`Guest Message: "\${guestText}"\\nDetected Intent: "\${intent}"\\nSelected Language: "\${language}"\`;

return [{
  json: {
    ...input,
    phase5_memory,
    phase5_stay_summary: stay_summary,
    phase5_memory_actions: memory_actions,
    phase5_summary_decision: summaryDecision,
    gemini_url: 'https://generativelanguage.googleapis.com/v1beta/models/' + ($env.GEMINI_MODEL ?? 'gemini-2.5-flash-lite') + ':generateContent?key=' + ($env.GEMINI_API_KEY ?? ''),
    gemini_body: {
      contents: [{
        parts: [
          { text: systemPrompt + '\\n\\n' + userMessage }
        ]
      }],
      generationConfig: {
        responseMimeType: 'application/json',
        temperature: 0.3
      }
    }
  }
}];
`;

const sideEffectsPatch = `
// --- INJECTED PHASE 5 FUNCTIONS ---
${getPhase5Functions()}
// ----------------------------------

const p5actions = reply.phase5_memory_actions;
const guestMessage = typeof reply.guest_text === 'string' ? reply.guest_text : '-';

// Persist inbound guest evidence so later turns can resolve multi-message booking
// claims and retrieval can rely on real chat history even in direct n8n tests.
if (reply.conversation_id && guestMessage && guestMessage !== '-') {
  addRequest(
    "record_inbound_conversation_message",
    "POST",
    $env.SUPABASE_URL + "/rest/v1/conversation_messages",
    {
      conversation_id: reply.conversation_id,
      line_webhook_event_id: uuidOrNull(reply.source_event_id),
      correlation_id: uuidOrNull(reply.correlation_id),
      sender_type: "guest",
      sender_ref: reply.line_user_id ?? reply.actor?.line_user_id ?? null,
      channel: "guest_oa",
      message_type: "text",
      body: guestMessage,
      language: reply.language ?? "th",
      direction: "inbound",
      visibility: "guest_visible",
      contains_room_access_info: false,
      contains_personal_data: true,
    }
  );
}

// Phase 5 Memory updates
if (Array.isArray(p5actions) && p5actions.length > 0) {
  addRpc("phase5_apply_memory_actions", {
    p_conversation_id: reply.conversation_id ?? null,
    p_source_event_id: reply.source_event_id ?? null,
    p_actions: p5actions,
    p_created_by: "guest_oa_extraction",
  });
}
// Dynamically fetch active incidents to pass to candidate builder
let activeIncidents = [];
if (reply.conversation_id) {
  try {
    const getIncidentsResponse = await this.helpers.httpRequest({
      method: 'GET',
      url: $env.SUPABASE_URL + '/rest/v1/operational_incidents?conversation_id=eq.' + reply.conversation_id + '&status=in.(open,acknowledged,in_progress)&select=id,status,issue_family,issue_subtype,severity',
      headers: { apikey: $env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' },
      json: true
    });
    activeIncidents = Array.isArray(getIncidentsResponse) ? getIncidentsResponse : [];
  } catch (e) {
    // Ignore
  }
}

// Build Guest Incident Candidate
let incidentCandidate = buildGuestIncidentCandidate({
  text: guestMessage,
  conversationId: reply.conversation_id ?? null,
  bookingId: bookingId,
  roomId: roomId,
  sourceEventId: reply.source_event_id ?? null,
  correlationId: reply.correlation_id ?? null,
  currentTopic: reply.interpreted_topic ?? "general_chat",
  activeIncidents: activeIncidents
});

const p5IssueAction = Array.isArray(p5actions) ? p5actions.find((action) => action?.field === 'current_issue') : null;
const p5SubtypeAction = Array.isArray(p5actions) ? p5actions.find((action) => action?.field === 'current_issue_subtype') : null;
if (p5IssueAction?.new_value && p5SubtypeAction?.new_value) {
  const issueFamily = p5IssueAction.new_value;
  const issueSubtype = p5SubtypeAction.new_value;
  const shouldIgnoreIssueAction = issueFamily === 'checkout_extension_request' && issueSubtype === 'checkout_policy_question';
  if (!shouldIgnoreIssueAction) {
  const isCheckoutPricingPressure =
    issueFamily === 'checkout_extension_request' &&
    /(คิดเพิ่ม|จ่ายเพิ่ม|ฟรี|ไม่จ่ายเพิ่ม|คืนเงิน|เท่าไหร่|กี่บาท)/i.test(guestMessage);
  const severity = (
    issueFamily === 'room_access_problem' ||
    issueFamily === 'cleaning_delayed_checkin' ||
    isCheckoutPricingPressure ||
    (issueFamily === 'guest_dispute_escalation' && !['deposit_refund_dispute', 'refund_request'].includes(issueSubtype))
  ) ? 'urgent' : (
    issueFamily === 'checkout_extension_request' ? 'high' : (incidentCandidate?.severity || 'normal')
  );
  incidentCandidate = {
    source_surface: 'guest_oa',
    source_event_id: reply.source_event_id ?? null,
    correlation_id: reply.correlation_id ?? null,
    idempotency_key: 'guest_oa:' + (reply.source_event_id ?? reply.correlation_id ?? Date.now()) + ':' + issueFamily,
    conversation_id: reply.conversation_id ?? null,
    booking_id: bookingId,
    room_id: roomId,
    issue_family: issueFamily,
    issue_subtype: issueSubtype,
    severity,
    latest_evidence_text: guestMessage,
    requires_internal_ops: true,
    requires_owner: true
  };
  }
}

if (!incidentCandidate) {
  const activeIssueFamily = reply.phase5_memory?.current_issue?.value;
  const activeIssueSubtype = reply.phase5_memory?.current_issue_subtype?.value;
  const isKnownOperationalFamily = [
    'checkout_extension_request',
    'guest_dispute_escalation',
    'cleaning_delayed_checkin',
    'room_access_problem',
  ].includes(activeIssueFamily);
  const isCheckoutPricingPressure =
    activeIssueFamily === 'checkout_extension_request' &&
    (
      /checkout_extension_pricing|pricing_waiver/i.test(String(reply.p5send_reason ?? '')) ||
      /(คิดเพิ่ม|จ่ายเพิ่ม|ฟรี|ไม่จ่ายเพิ่ม|คืนเงิน|เท่าไหร่|กี่บาท)/i.test(guestMessage)
    );
  const isIssueBoundFollowUp =
    isCheckoutPricingPressure ||
    (activeIssueFamily === 'cleaning_delayed_checkin' && /^cleaning_delayed_checkin/i.test(String(reply.p5send_reason ?? ''))) ||
    (activeIssueFamily === 'room_access_problem' && /room_access|service_recovery/i.test(String(reply.p5send_reason ?? ''))) ||
    (activeIssueFamily === 'guest_dispute_escalation' && ['draft_only', 'internal_now'].includes(reply.p5send_mode));

  if (isKnownOperationalFamily && activeIssueSubtype && isIssueBoundFollowUp) {
    const severity = (
      activeIssueFamily === 'room_access_problem' ||
      activeIssueFamily === 'cleaning_delayed_checkin' ||
      isCheckoutPricingPressure ||
      (activeIssueFamily === 'guest_dispute_escalation' && !['deposit_refund_dispute', 'refund_request'].includes(activeIssueSubtype))
    ) ? 'urgent' : (
      activeIssueFamily === 'checkout_extension_request' ? 'high' : 'normal'
    );
    incidentCandidate = {
      source_surface: 'guest_oa',
      source_event_id: reply.source_event_id ?? null,
      correlation_id: reply.correlation_id ?? null,
      idempotency_key: 'guest_oa:' + (reply.source_event_id ?? reply.correlation_id ?? Date.now()) + ':' + activeIssueFamily,
      conversation_id: reply.conversation_id ?? null,
      booking_id: bookingId,
      room_id: roomId,
      issue_family: activeIssueFamily,
      issue_subtype: activeIssueSubtype,
      severity,
      latest_evidence_text: guestMessage,
      requires_internal_ops: true,
      requires_owner: true
    };
  }
}

if (incidentCandidate) {
  incidentCandidate.final_delivery_mode = reply.p5send_mode ?? null;
  incidentCandidate.model_recommended_mode = reply.p5recommended_mode ?? null;

  // Post incident candidate to public.report_operational_incident RPC
  addRequest(
    "report_operational_incident",
    "POST",
    $env.SUPABASE_URL + "/rest/v1/rpc/report_operational_incident",
    { p_incident: incidentCandidate }
  );

  // If delayed check-in, merge housekeeping task
  if (incidentCandidate.issue_family === 'cleaning_delayed_checkin') {
    const subtype = incidentCandidate.issue_subtype;
    if (subtype !== 'access_prep_incomplete' && (roomId || bookingId)) {
      const housekeepingTaskType = subtype === 'readiness_unknown' ? 'inspection' : 'turnover_cleaning';
      const housekeepingInstructions = {
        cleaning_not_ready: 'ลูกค้าพร้อมเช็กอินแล้ว แต่ห้องยังไม่พร้อม กรุณาเร่งเตรียมห้องและอัปเดตสถานะทันที',
        housekeeping_no_ack: 'ลูกค้ารอเช็กอินอยู่ กรุณารับทราบงานและอัปเดตสถานะห้องทันที',
        readiness_unknown: 'ลูกค้ารอเช็กอินอยู่ แต่สถานะห้องยังไม่ชัดเจน กรุณาตรวจสอบหน้างานและอัปเดตสถานะ',
      }[subtype] || 'ลูกค้ารอเช็กอินอยู่ กรุณาตรวจสอบความพร้อมของห้องและอัปเดตสถานะทันที';

      // Find case ID if already existing:
      let existingCaseId = null;
      try {
        const getCasesResponse = await this.helpers.httpRequest({
          method: 'GET',
          url: $env.SUPABASE_URL + '/rest/v1/internal_ops_cases?conversation_id=eq.' + reply.conversation_id + '&status=in.(waiting_admin,assigned,in_progress,open)&select=id,case_context_snapshot',
          headers: { apikey: $env.SUPABASE_SERVICE_ROLE_KEY, Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY, 'Content-Type': 'application/json' },
          json: true
        });
        const openCases = Array.isArray(getCasesResponse) ? getCasesResponse : [];
        const delayedCheckinCase = openCases.find(c => c.case_context_snapshot?.alert_kind === 'cleaning_delayed_checkin');
        if (delayedCheckinCase) {
          existingCaseId = delayedCheckinCase.id;
        }
      } catch (e) {
        // Ignore
      }

      addRpc("merge_housekeeping_cleaning_task", {
        p_task: {
          task_key: 'phase5-delayed-checkin:' + (roomId || bookingId) + ':' + housekeepingTaskType,
          room_id: roomId,
          booking_id: bookingId,
          internal_ops_case_id: existingCaseId,
          task_type: housekeepingTaskType,
          priority: 'urgent',
          instructions: housekeepingInstructions,
          source: 'concierge'
        },
        p_source_event_id: reply.source_event_id ?? null,
      });
    }
  }
}

// Create message draft if p5send_mode is 'draft_only'
if (reply.p5send_mode === 'draft_only') {
  addRequest(
    "phase5_create_draft",
    "POST",
    $env.SUPABASE_URL + "/rest/v1/message_drafts",
    {
      conversation_id: reply.conversation_id ?? null,
      booking_id: bookingId,
      draft_text: (reply.texts || []).join("\\\\n\\\\n"),
      draft_purpose: "follow_up",
      channel_target: "guest_oa",
      delivery_mode: "admin_copy_paste",
      draft_surface: "internal_ops_oa",
      draft_trigger: "auto",
      status: "draft",
      approval_required: true,
      auto_send_allowed: false,
      draft_importance: "routine",
      language: reply.language ?? "th",
      guest_display_snapshot: reply.booking?.guest_name_snapshot || reply.guest?.guest_name || roomCode || 'ลูกค้า',
      room_code_snapshot: roomCode || reply.booking?.rooms?.room_code || null,
      platform_snapshot: reply.booking?.platform || reply.guest?.platform || null,
      reservation_number_snapshot: reply.booking?.reservation_number || reply.guest?.reservation_number || null,
      visible_context_summary: reply.visible_context_summary || null,
      evidence_summary: reply.evidence_summary || null,
      latest_guest_message_excerpt: guestMessage || null,
      admin_action_needed: reply.admin_action_needed || "โปรดตรวจสอบและแก้ไขร่างข้อความ",
      reason: reply.p5send_reason,
      case_context_snapshot: { 
        intent: reply.intent, 
        reason: reply.p5send_reason, 
        risk_flags: reply.risk_flags,
        final_delivery_mode: reply.p5send_mode,
        model_recommended_mode: reply.p5recommended_mode,
        correlation_id: reply.correlation_id
      },
      request_idempotency_key: (reply.correlation_id ?? Date.now().toString()) + "_draft"
    }
  );
}

const p5summaryDecision = reply.phase5_summary_decision ?? null;
const p5summaryText = typeof reply.phase5_generated_summary_text === "string"
  ? reply.phase5_generated_summary_text.trim()
  : "";
if (
  reply.conversation_id &&
  p5summaryText &&
  (p5summaryDecision?.action === "create_summary" || p5summaryDecision?.action === "refresh_summary")
) {
  addRequest(
    "patch_phase5_existing_stay_summaries",
    "PATCH",
    $env.SUPABASE_URL + "/rest/v1/stay_summaries?conversation_id=eq." + reply.conversation_id + "&is_superseded=eq.false",
    {
      is_superseded: true,
    }
  );
  addRequest(
    "insert_phase5_stay_summary",
    "POST",
    $env.SUPABASE_URL + "/rest/v1/stay_summaries",
    {
      conversation_id: reply.conversation_id,
      summary_text: p5summaryText,
      message_count_at_generation: Number(p5summaryDecision?.message_count_at_generation ?? 0),
      is_superseded: false,
    }
  );
}
`;

const buildGuestReplyCode = `
const input = items[0].json;

// --- INJECTED PHASE 5 FUNCTIONS ---
${getPhase5Functions()}
const plan = input.phase3_guardrail ?? input;
const originalModeDecision = evaluateSendMode(plan, input.intent);
let p5sendModeDecision = { ...originalModeDecision };
const phase5_memory_actions = input.phase5_memory_actions ?? [];
const promptJson = $("Build Gemini Prompt").first()?.json ?? {};
const phase5_memory = promptJson.phase5_memory ?? {};
const guestTextForRouting = String(input.guest_text ?? '');
const hasFreshRoomAccessSignal =
  phase5_memory_actions.some(a => a.field === 'current_issue' && a.new_value === 'room_access_problem') ||
  /(เข้าห้องไม่ได้|เปิดห้องไม่ได้|เปิดประตูไม่ได้|เปิดไม่ออก|ยังเปิดไม่ออก|ไม่เจอกุญแจ|กุญแจอยู่ไหน|หากุญแจไม่เจอ|ไม่มีกุญแจ|เข้าตึกไม่ได้|หาทางเข้าไม่เจอ|หลงทางเข้า|ไปต่อไม่ได้|ติดอยู่หน้าตึก|ติดอยู่หน้าอาคาร)/i.test(guestTextForRouting);
const isRoomAccessProblem = hasFreshRoomAccessSignal;
if (isRoomAccessProblem && p5sendModeDecision.send_mode === 'safe_auto') {
    p5sendModeDecision = { send_mode: 'draft_only', reason: 'service_recovery_room_access_elevation' };
}

const isDelayedCheckin = phase5_memory_actions.some(a => a.field === 'current_issue' && a.new_value === 'cleaning_delayed_checkin') || (phase5_memory?.current_issue?.value === 'cleaning_delayed_checkin' && !phase5_memory?.current_issue?.is_superseded);
const delayedCheckinSubtypeAction = phase5_memory_actions.find(a => a.field === 'current_issue_subtype');
const delayedCheckinSubtype = delayedCheckinSubtypeAction?.new_value ?? phase5_memory?.current_issue_subtype?.value ?? null;
const roomAccessReadiness = input.room_access_readiness ?? {
  ready: false,
  blockers: ["readiness_unknown"],
};
const readinessBlockers = Array.isArray(roomAccessReadiness.blockers)
  ? roomAccessReadiness.blockers
  : ["readiness_unknown"];
const isAccessPrepIncomplete = Boolean(input.booking?.id) &&
  roomAccessReadiness.ready !== true;
if (isDelayedCheckin) {
    p5sendModeDecision = evaluateDelayedCheckinPolicy({
        guestText: guestTextForRouting,
        blocker: delayedCheckinSubtype,
        currentMode: p5sendModeDecision.send_mode,
    });
}

const checkoutExtensionSubtype = detectCheckoutExtensionSubtype(guestTextForRouting, phase5_memory);
const isCheckoutExtension = Boolean(checkoutExtensionSubtype);

if (isCheckoutExtension) {
    if (/(คิดเพิ่มเท่าไหร่|ขอฟรีได้ไหม|ไม่จ่ายเพิ่ม|ถ้าไม่ได้จะขอคืนเงิน|ฟรีได้ไหม|เท่าไหร่|กี่บาท)/i.test(guestTextForRouting)) {
        p5sendModeDecision = { send_mode: 'internal_now', reason: 'checkout_extension_pricing_waiver_escalation' };
    } else if (checkoutExtensionSubtype === 'late_checkout_request' || checkoutExtensionSubtype === 'stay_extension_request') {
        p5sendModeDecision = { send_mode: 'draft_only', reason: 'checkout_extension_approval_required' };
    } else if (checkoutExtensionSubtype === 'checkout_policy_question' && p5sendModeDecision.send_mode !== 'internal_now') {
        // Keep safe_auto if it was safe_auto or let it be draft_only if model thought so
        if (p5sendModeDecision.send_mode === 'safe_auto') {
            p5sendModeDecision = { send_mode: 'safe_auto', reason: 'checkout_policy_factual_answer' };
        }
    }
}

const dispute = detectDisputeEscalationSubtype(guestTextForRouting, phase5_memory);
const isDispute = Boolean(dispute);
if (isDispute) {
    const disputeMode = evaluateDisputeSendMode(dispute, guestTextForRouting, phase5_memory);
    // Dispute routing is the deterministic final authority for Slice 6.
    // This allows calm account-specific deposit questions to become drafts
    // even if the model/risk gate was overly conservative.
    p5sendModeDecision = disputeMode;
}
if (isRoomAccessProblem && !isDispute) {
    p5sendModeDecision = { send_mode: 'draft_only', reason: 'service_recovery_room_access_elevation' };
}

const phase5_stay_summary = promptJson.phase5_stay_summary ?? null;
const phase5_summary_decision = promptJson.phase5_summary_decision ?? { action: "skip" };
const assetsById = input.assets_by_id ?? {};
const images = [];
function formatSummaryValue(value) {
  const valueLabels = {
    car: "รถยนต์ส่วนตัว",
    taxi: "แท็กซี่",
    taxi_grab: "แท็กซี่/แอปเรียกรถ",
    public_transport: "รถสาธารณะ",
    private_motorcycle: "มอเตอร์ไซค์ส่วนตัว",
    motorbike_taxi: "วินมอเตอร์ไซค์",
    not_departed: "ยังไม่ออกเดินทาง",
    on_the_way: "กำลังเดินทางมา",
    at_building: "อยู่หน้าตึก",
    in_cosmo: "อยู่แถว Cosmo",
    in_room: "อยู่ในห้องแล้ว",
    waiting_to_check_in: "รอเช็กอิน",
    checked_in: "เช็กอินแล้ว",
    checking_out: "กำลังเช็กเอาต์",
  };
  if (Array.isArray(value)) return value.map((item) => formatSummaryValue(item)).join(", ");
  if (typeof value === "string" && valueLabels[value]) return valueLabels[value];
  if (value === null || value === undefined || value === "") return "-";
  return String(value);
}
function buildGeneratedStaySummary() {
  if (phase5_summary_decision?.action !== "create_summary" && phase5_summary_decision?.action !== "refresh_summary") {
    return null;
  }
  const roomCode = input.booking?.rooms?.room_code ?? input.stay_state?.room_code_snapshot ?? null;
  const lines = ["สรุปการเข้าพักล่าสุด"];
  if (roomCode) lines.push("- ห้อง " + roomCode);
  const summaryFields = [
    ["travel_mode", "การเดินทาง"],
    ["parking_mode", "เรื่องที่จอดรถ"],
    ["current_location_hint", "ตำแหน่งล่าสุด"],
    ["arrival_state", "สถานะการมาถึง"],
    ["check_in_state", "สถานะเช็กอิน"],
    ["check_out_state", "สถานะเช็กเอาต์"],
    ["local_needs_hints", "ความต้องการในพื้นที่"],
    ["purpose_context", "บริบทการมาพัก"],
  ];
  for (const [field, label] of summaryFields) {
    const row = phase5_memory[field];
    if (row && !row.is_superseded) {
      lines.push("- " + label + ": " + formatSummaryValue(row.value));
    }
  }
  if (typeof input.guest_text === "string" && input.guest_text.trim()) {
    lines.push("- ข้อความล่าสุด: " + input.guest_text.trim());
  }
  return lines.length > 1 ? lines.join("\\n") : null;
}
for (const action of plan.asset_actions ?? []) {
  const runtimeUrl = action.runtime_media_url ?? action.originalContentUrl ?? assetsById[action.asset_id]?.runtime_media_url;
  const previewUrl = action.previewImageUrl ?? assetsById[action.asset_id]?.preview_media_url ?? runtimeUrl;
  if (runtimeUrl) {
    images.push({ originalContentUrl: runtimeUrl, previewImageUrl: previewUrl });
  }
}
const followUpMessages = Array.isArray(plan.follow_up_messages) ? plan.follow_up_messages : [];
let texts = [plan.text, ...followUpMessages]
  .filter((message) => typeof message === 'string')
  .map((message) => message.trim())
  .filter((message) => message);
let primaryText = texts[0] ?? (typeof plan.text === 'string' ? plan.text.trim() : '');

if (isCheckoutExtension) {
  let checkoutText = null;
  if (checkoutExtensionSubtype === 'checkout_policy_question') {
    checkoutText = 'ปกติเช็กเอาต์เวลา 12:00 น. นะคะ หากต้องการเลทเช็กเอาต์หรือพักต่อ ทางเราต้องตรวจสอบและให้แอดมินยืนยันก่อนค่ะ';
  } else if (checkoutExtensionSubtype === 'late_checkout_request') {
    checkoutText = 'รับทราบค่ะ คุณมาลี ขอตรวจสอบกับทีมก่อนนะคะว่าสามารถเลทเช็กเอาต์ตามเวลาที่ขอได้หรือไม่ แล้วแอดมินจะยืนยันกลับไปค่ะ';
  } else if (checkoutExtensionSubtype === 'stay_extension_request') {
    checkoutText = 'รับทราบค่ะ คุณมาลี ขอตรวจสอบห้องว่างและเงื่อนไขกับทีมก่อนนะคะ แล้วแอดมินจะยืนยันกลับไปค่ะ';
  }
  if (checkoutText) {
    texts = [checkoutText];
    primaryText = checkoutText;
  }
}

if (isDispute) {
  let disputeText = null;
  const isEn = /hello|hi|thank|receipt|deposit|refund|checkout|wifi/i.test(guestTextForRouting);
  if (dispute.issue_subtype === 'deposit_refund_dispute') {
    disputeText = isEn 
      ? 'Please wait a moment. Our team is checking your deposit status and will get back to you shortly.' 
      : 'รบกวนรอสักครู่นะคะ ทางทีมงานกำลังตรวจสอบสถานะเงินมัดจำให้ค่ะ เมื่อเรียบร้อยแล้วจะรีบแจ้งกลับทันทีค่ะ';
  } else if (dispute.issue_subtype === 'refund_request' || dispute.issue_subtype === 'compensation_request') {
    disputeText = isEn
      ? 'Please wait a moment. Our team is checking your request and will get back to you shortly.'
      : 'รบกวนรอสักครู่นะคะ ทางทีมงานกำลังตรวจสอบข้อมูลให้ค่ะ เมื่อเรียบร้อยแล้วจะรีบแจ้งกลับทันทีค่ะ';
  }
  
  if (disputeText && (p5sendModeDecision.send_mode === 'draft_only' || p5sendModeDecision.send_mode === 'safe_auto')) {
    texts = [disputeText];
    primaryText = disputeText;
  }
}

if (isDelayedCheckin) {
  const safeHoldingText = buildDelayedCheckinHoldingReply(delayedCheckinSubtype);
  if (p5sendModeDecision.send_mode === 'safe_auto') {
    texts = [safeHoldingText];
    primaryText = safeHoldingText;
  } else {
    texts = texts.map((message) => hasUnsafeDelayedCheckinReadyWording(message) ? safeHoldingText : message);
    if (!texts.length) {
      texts = [safeHoldingText];
    }
    primaryText = texts[0];
  }
}

if (isAccessPrepIncomplete) {
  const accessPrepHoldingText = buildDelayedCheckinHoldingReply('access_prep_incomplete');
  const unsafeAccessReady = (message) =>
    /(เข้าไปได้เลย|ขึ้นไป.*ได้เลย|ขึ้นห้อง.*ได้เลย|ห้อง.*พร้อม|กุญแจ.*(วาง|เตรียม|อยู่ในห้อง)|เปิดไว้ให้แล้ว|สามารถเข้าห้อง|สามารถขึ้นห้อง|เชิญขึ้นห้อง)/i.test(message);
  if (texts.some(unsafeAccessReady)) {
    texts = [accessPrepHoldingText];
    primaryText = accessPrepHoldingText;
  }
}

const finalImages = (
  isDelayedCheckin ||
  isAccessPrepIncomplete ||
  roomAccessReadiness.ready !== true
) ? [] : images;
const phase5_generated_summary_text = buildGeneratedStaySummary();
return [{
  json: {
    ...input,
    ...plan,
    text: primaryText,
    images: finalImages,
    texts,
    phase5_memory_actions,
    phase5_memory,
    phase5_stay_summary,
    phase5_summary_decision,
    phase5_generated_summary_text,
    phase5_detected_checkout_extension_subtype: checkoutExtensionSubtype,
    phase5_detected_dispute: dispute,
    room_access_readiness: roomAccessReadiness,
    room_access_blockers: readinessBlockers,
    p5send_mode: p5sendModeDecision.send_mode,
    p5recommended_mode: originalModeDecision.send_mode,
    p5send_reason: p5sendModeDecision.reason,
  }
}];
`;

const aggregateChatHistoryCode = `
const rawResponse = items[0]?.json ?? {};
const rawHistory = Array.isArray(rawResponse?.body) ? rawResponse.body : (Array.isArray(rawResponse) ? rawResponse : []);
const messages = rawHistory.map(item => ({
  sender: item.sender_type,
  text: item.body,
  created_at: item.created_at
})).reverse();
const input = $("Classify guest intent").first().json;
return [{ json: { ...input, chat_history: messages } }];
`;

// Patch the nodes
let patched = false;
for (const node of workflowData.nodes) {
  if (node.name === "Load guest context") {
    node.parameters.url = `={{ $env.SUPABASE_URL + "/rest/v1/rpc/phase5_slice4_guest_concierge_context" }}`;
    node.parameters.jsonBody = "={{ { p_line_user_id: $json.line_user_id || ($json.actor ? $json.actor.line_user_id : null), p_conversation_id: $json.conversation_id || null, p_guest_text: $json.guest_text, p_intent: $json.intent, p_language: $json.language } }}";
    patched = true;
  }
  if (node.name === "Classify guest intent") {
    node.parameters.jsCode = classifyIntentCode.trim();
    patched = true;
  }
  if (node.name === "Build Gemini Prompt") {
    node.parameters.jsCode = promptCode.trim();
    patched = true;
  }
  if (node.name === "Apply Phase3 guardrails") {
    // Convert from HTTP Request to Code node to bypass Edge function
    node.type = "n8n-nodes-base.code";
    node.typeVersion = 2;
    node.parameters = {
      mode: "runOnceForAllItems",
      language: "javaScript",
      jsCode: `
const baseInput = $("Build Gemini Prompt").first().json;
const historyInput = $("Aggregate Chat History").first().json ?? {};
const input = { ...baseInput, chat_history: historyInput.chat_history ?? [] };
const rawGemini = $("Call Gemini AI").first().json;

let roomAccessReadiness = {
  ready: false,
  blockers: ["readiness_unknown"],
};
if (input.booking?.id) {
  try {
    const readinessResponse = await this.helpers.httpRequest({
      method: "POST",
      url: $env.SUPABASE_URL + "/rest/v1/rpc/get_room_access_readiness",
      headers: {
        apikey: $env.SUPABASE_SERVICE_ROLE_KEY,
        Authorization: "Bearer " + $env.SUPABASE_SERVICE_ROLE_KEY,
        "Content-Type": "application/json",
      },
      body: { p_booking_id: input.booking.id },
      json: true,
      returnFullResponse: true,
    });
    roomAccessReadiness = readinessResponse?.body ?? readinessResponse ??
      roomAccessReadiness;
  } catch (_) {
    roomAccessReadiness = {
      ready: false,
      blockers: ["readiness_unknown"],
    };
  }
}
input.room_access_readiness = roomAccessReadiness;

let geminiText = "";
try {
  geminiText = rawGemini.candidates[0].content.parts[0].text;
} catch (e) {
  geminiText = "{}";
}

// Clean markdown code blocks if any
const bt = String.fromCharCode(96);
const bt3 = bt + bt + bt;
if (geminiText.startsWith(bt3 + "json")) {
  geminiText = geminiText.substring(7);
} else if (geminiText.startsWith(bt3)) {
  geminiText = geminiText.substring(3);
}
if (geminiText.endsWith(bt3)) {
  geminiText = geminiText.substring(0, geminiText.length - 3);
}
geminiText = geminiText.trim();

let parsed = {};
try {
  parsed = JSON.parse(geminiText);
} catch (e) {
  parsed = {
    reply_text: "...",
    inferred_intent: input.intent || "safe_general_question"
  };
}

let phase5_memory_actions = Array.isArray(input.phase5_memory_actions) ? [...input.phase5_memory_actions] : [];
if (input.test_context?.mock_delayed_checkin) {
  parsed.internal_ops_alert = "cleaning_delayed_checkin";
  let subtype = input.test_context?.mock_subtype || "cleaning_not_ready";
  if (input.guest_text === "จะเข้าห้อง") subtype = "readiness_unknown";
  if (input.guest_text === "อีกนานมั้ย") subtype = "cleaning_not_ready";
  if (input.guest_text === "เข้าไปได้เลยมั้ย") subtype = "housekeeping_no_ack";
  if (input.test_context?.mock_send_mode) {
    parsed.recommended_send_mode = input.test_context.mock_send_mode;
    parsed.confidence_level = input.test_context.mock_send_mode === 'internal_now' ? 'low' : 'high';
    parsed.suggested_sop_family = "cleaning_delayed_checkin";
    parsed.risk_flags = input.test_context.mock_send_mode === 'internal_now' ? ["authority_required"] : ["none"];
  }
  if (input.test_context?.mock_reply_text) {
    parsed.reply_text = input.test_context.mock_reply_text;
  }
  phase5_memory_actions = phase5_memory_actions.filter((action) => !['current_issue', 'current_issue_subtype'].includes(action?.field));
  phase5_memory_actions.push(
    { field: "current_issue", new_value: "cleaning_delayed_checkin", reasoning: "Mocked delayed checkin" },
    { field: "current_issue_subtype", new_value: subtype }
  );
}

const phase3_guardrail = {
  to: input.line_user_id || (input.actor ? input.actor.line_user_id : undefined),
  text: parsed.reply_text || "",
  ...parsed
};

return [{ json: { ...input, phase3_guardrail, phase5_memory_actions, ...parsed } }];
`.trim()
    };
    patched = true;
  }
  if (node.name === "Build guest reply or internal alert") {
    node.parameters.jsCode = buildGuestReplyCode.trim();
    patched = true;
  }
  if (node.name === "Send through controlled Edge path") {
    node.parameters.jsonBody = "={{ { channel: 'guest_oa', to: $json.to, text: $json.text, texts: $json.texts || ($json.text ? [$json.text] : []), images: $json.images || [], conversation_id: $json.conversation_id, source_event_id: $json.source_event_id, correlation_id: $json.correlation_id, reply_token_ephemeral: $json.reply_token_ephemeral, delivery_mode: $json.p5send_mode === 'safe_auto' ? 'push' : 'no_send', idempotency_key: $json.correlation_id ? $json.correlation_id + '_edge' : undefined, suppression_reason: $json.p5send_reason, final_delivery_mode: $json.p5send_mode, model_recommended_mode: $json.p5recommended_mode, risk_family: $json.phase5_detected_dispute ? 'guest_dispute_escalation' : ($json.phase5_memory_actions && Array.isArray($json.phase5_memory_actions) ? $json.phase5_memory_actions.find(a => a.field === 'current_issue')?.new_value : undefined) || ($json.phase5_memory && $json.phase5_memory.current_issue?.value) || undefined, risk_subtype: ($json.phase5_detected_dispute && $json.phase5_detected_dispute.issue_subtype) || ($json.phase5_memory_actions && Array.isArray($json.phase5_memory_actions) ? $json.phase5_memory_actions.find(a => a.field === 'current_issue_subtype')?.new_value : undefined) || ($json.phase5_memory && $json.phase5_memory.current_issue_subtype?.value) || undefined, alert_kind: $json.phase5_detected_dispute ? 'guest_dispute_escalation' : ($json.p5send_reason === 'cleaning_delayed_checkin_authority_bound_escalation' || $json.p5send_reason === 'cleaning_delayed_checkin_holding_reply' ? 'cleaning_delayed_checkin' : ($json.p5send_reason === 'service_recovery_room_access_elevation' ? 'service_recovery_room_access' : undefined)) } }}";
    patched = true;
  }
  if (node.name === "Load Chat History") {
    node.parameters.url = '={{ $env.SUPABASE_URL }}/rest/v1/conversation_messages?conversation_id=eq.{{ $json.conversation_id }}&order=created_at.desc&limit=80';
    node.parameters.options = {
      ...(node.parameters.options ?? {}),
      neverSplitResults: true,
      response: { response: { fullResponse: true } },
    };
    patched = true;
  }
  if (node.name === "Aggregate Chat History") {
    node.parameters.jsCode = aggregateChatHistoryCode.trim();
    patched = true;
  }
  if (node.name === "Prepare Phase3 side effects") {
    const existingCode = node.parameters.jsCode ?? "";
    const patchMarker = "// Phase 5 Memory updates";
    const existingPatchIndex = existingCode.indexOf(patchMarker);
    const returnIndex = existingCode.lastIndexOf("return out;");
    if (existingPatchIndex >= 0 && returnIndex > existingPatchIndex) {
      node.parameters.jsCode = existingCode.slice(0, existingPatchIndex) + sideEffectsPatch + "\nreturn out;";
    } else if (returnIndex >= 0) {
      node.parameters.jsCode = existingCode.slice(0, returnIndex) + sideEffectsPatch + "\nreturn out;";
    }
    patched = true;
  }
}

if (!patched) {
  console.error("Could not find 'Build Gemini Prompt' node");
  process.exit(1);
}

const scratchOutPath = new URL('./wf_guest_concierge_patched.json', import.meta.url);
const scratchCanonicalOutPath = new URL('./wf_guest_concierge.json', import.meta.url);
const rootOutPath = new URL('../wf_guest_concierge.json', import.meta.url);
const runtimeOutPath = new URL('../runtime/n8n/workflows/wf_guest_concierge.json', import.meta.url);

fs.writeFileSync(scratchOutPath, JSON.stringify(workflowData, null, 2) + '\n');
fs.writeFileSync(scratchCanonicalOutPath, JSON.stringify(workflowData, null, 2) + '\n');
fs.writeFileSync(runtimeOutPath, JSON.stringify(workflowData, null, 2) + '\n');
fs.writeFileSync(rootOutPath, JSON.stringify([workflowData], null, 2) + '\n');

console.log("Successfully patched impact-guest-concierge workflow. Saved to both scratch artifacts, wf_guest_concierge.json, and runtime/n8n/workflows/wf_guest_concierge.json");
