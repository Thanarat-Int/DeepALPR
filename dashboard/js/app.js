/* ===== Deep ALPR · Access Control — single page app ===== */
(() => {
"use strict";

/* ---------- icons ---------- */
const ICONS = {
  grid:'<rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/>',
  list:'<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><circle cx="3.6" cy="6" r="1.3"/><circle cx="3.6" cy="12" r="1.3"/><circle cx="3.6" cy="18" r="1.3"/>',
  car:'<path d="M5 11l1.6-4.6A2 2 0 0 1 8.5 5h7a2 2 0 0 1 1.9 1.4L19 11"/><path d="M3 11h18v5a1 1 0 0 1-1 1h-1.5v1.5a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1V17H9.5v1.5a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1V17H4a1 1 0 0 1-1-1z"/><circle cx="7.5" cy="14" r="1"/><circle cx="16.5" cy="14" r="1"/>',
  ban:'<circle cx="12" cy="12" r="9"/><line x1="5.6" y1="5.6" x2="18.4" y2="18.4"/>',
  chart:'<line x1="3" y1="21" x2="21" y2="21"/><rect x="5" y="10" width="3.5" height="9"/><rect x="10.4" y="5" width="3.5" height="14"/><rect x="15.8" y="13" width="3.5" height="6"/>',
  settings:'<line x1="4" y1="7" x2="20" y2="7"/><circle cx="9" cy="7" r="2.3"/><line x1="4" y1="17" x2="20" y2="17"/><circle cx="15" cy="17" r="2.3"/>',
  search:'<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.6" y2="16.6"/>',
  plus:'<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  edit:'<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
  trash:'<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>',
  logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
  check:'<path d="M20 6L9 17l-5-5"/>',
  x:'<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  alert:'<path d="M10.3 3.8 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13.5"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  clock:'<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>',
  scan:'<path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2"/><line x1="4" y1="12" x2="20" y2="12"/>',
  plate:'<rect x="2.4" y="6.4" width="19.2" height="11.2" rx="2.7"/><line x1="7" y1="10.6" x2="7" y2="13.4"/><line x1="10.33" y1="10.6" x2="10.33" y2="13.4"/><line x1="13.67" y1="10.6" x2="13.67" y2="13.4"/><line x1="17" y1="10.6" x2="17" y2="13.4"/>',
  gate:'<path d="M4 21V7M4 7l16-3M4 12l16-3M4 17l16-3"/>',
  refresh:'<polyline points="21 4 21 9 16 9"/><path d="M19 9A8 8 0 1 0 5 6.5L3 9"/>',
  pin:'<path d="M12 21s-7-5.6-7-11a7 7 0 0 1 14 0c0 5.4-7 11-7 11z"/><circle cx="12" cy="10" r="2.3"/>',
  video:'<rect x="2.5" y="6" width="13" height="12" rx="2.5"/><path d="M15.5 10l6-3.3v10.6l-6-3.3z"/>',
  menu:'<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>',
  send:'<line x1="21" y1="3" x2="10.5" y2="13.5"/><polygon points="21 3 14.5 21 10.5 13.5 3 9.5 21 3"/>',
  lock:'<rect x="4" y="10.5" width="16" height="11" rx="2.2"/><path d="M7 10.5V7a5 5 0 0 1 10 0v3.5"/>',
  download:'<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M5 5l1.4 1.4M17.6 17.6 19 19M2 12h2M20 12h2M5 19l1.4-1.4M17.6 6.4 19 5"/>',
  moon:'<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
};
const icon = (n, s=20) =>
  `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${ICONS[n]||""}</svg>`;

/* ---------- i18n ---------- */
const STR = {
th:{
  app_tag:"Access Control", menu:"เมนูหลัก",
  nav_console:"แดชบอร์ด", nav_log:"ประวัติการเข้าออก", nav_vehicles:"ทะเบียนรถ",
  nav_blacklist:"บัญชีดำ", nav_reports:"รายงาน", nav_settings:"ตั้งค่าระบบ",
  sub_console:"ภาพรวมการเข้าออกแบบเรียลไทม์", sub_log:"บันทึกการผ่านเข้าออกทั้งหมด",
  sub_vehicles:"รถที่ลงทะเบียนในระบบ", sub_blacklist:"ทะเบียนที่ถูกระงับการเข้า",
  sub_reports:"สถิติและแนวโน้มการใช้งาน", sub_settings:"ผู้ใช้งานและการเชื่อมต่อ",
  role_admin:"ผู้ดูแลระบบ", role_operator:"เจ้าหน้าที่", logout:"ออกจากระบบ",
  login_sub:"Access Control System", f_username:"ชื่อผู้ใช้", f_password:"รหัสผ่าน",
  signin:"เข้าสู่ระบบ", signing:"กำลังเข้าสู่ระบบ", demo_accounts:"บัญชีทดสอบ",
  err_cred:"ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", err_conn:"เชื่อมต่อเซิร์ฟเวอร์ไม่ได้",
  d_granted:"อนุญาต", d_denied:"ปฏิเสธ", d_alert:"เฝ้าระวัง",
  d_granted_full:"อนุญาตให้ผ่าน", d_denied_full:"ปฏิเสธการเข้า", d_alert_full:"ตรวจสอบ รถไม่ลงทะเบียน",
  v_resident:"ลูกบ้าน", v_staff:"พนักงาน", v_visitor:"ผู้มาเยือน",
  s_today:"การเข้าออกวันนี้", s_granted:"อนุญาตผ่าน", s_denied:"ปฏิเสธ", s_alert:"เฝ้าระวัง",
  recent:"เหตุการณ์ล่าสุด", live:"สด",
  welcome:"ยินดีต้อนรับ", welcome_sub:"ภาพรวมกิจกรรมและสรุปการเข้าออกของคุณ",
  live_camera:"กล้องวงจรปิดสด", not_connected:"ยังไม่เชื่อมต่อ",
  live_cam_msg:"ภาพสดจากกล้องจะแสดงที่นี่",
  live_cam_note:"ฟีเจอร์อนาคต เปิดใช้งานเมื่อเชื่อมต่อกล้อง IP ผ่าน RTSP",
  retention_label:"นโยบายเก็บภาพ", retention_val:"90 วัน",
  pipe_title:"ขั้นตอนการทำงานของระบบ",
  pipe_capture:"รับภาพกล้อง", pipe_detect:"ตรวจจับป้าย", pipe_ocr:"อ่านทะเบียน",
  pipe_decide:"ตรวจสิทธิ์", pipe_log:"บันทึก และส่ง API",
  account:"บัญชีของฉัน", change_pw:"เปลี่ยนรหัสผ่าน", m_change_pw:"เปลี่ยนรหัสผ่าน",
  f_current_pass:"รหัสผ่านปัจจุบัน", f_new_pass:"รหัสผ่านใหม่",
  f_confirm_pass:"ยืนยันรหัสผ่านใหม่", pw_mismatch:"รหัสผ่านใหม่ไม่ตรงกัน",
  pw_short:"รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร", pw_changed:"เปลี่ยนรหัสผ่านเรียบร้อย",
  m_edit_user:"แก้ไขผู้ใช้งาน", q_del_user:"ลบบัญชีผู้ใช้นี้",
  f_new_pass_optional:"รหัสผ่านใหม่ (เว้นว่างไว้คือไม่เปลี่ยน)",
  c_owner:"เจ้าของ", c_type:"ประเภท", c_speed:"ความเร็ว", c_conf:"ความมั่นใจ OCR", c_time:"เวลา",
  c_color:"สีรถ", c_brand:"รุ่นรถ", c_year:"ปีจดทะเบียน",
  connecting:"กำลังเชื่อมต่อ", connected:"กำลังถ่ายทอด", demo_preview:"ตัวอย่าง (demo)",
  unknown:"ไม่ทราบ", no_events:"ยังไม่มีเหตุการณ์", no_image:"ไม่มีภาพถ่าย",
  open_gate:"เปิดไม้กั้น", approve:"อนุมัติด้วยตนเอง",
  gate_opened:"เปิดไม้กั้นแล้ว (จำลอง)", approved:"อนุมัติเรียบร้อย", unregistered:"รถไม่ลงทะเบียน",
  search_plate:"ค้นหาทะเบียน", all_results:"ทุกผลลัพธ์", refresh:"รีเฟรช", load_more:"โหลดเพิ่ม",
  th_image:"ภาพ", th_plate:"ทะเบียน", th_result:"ผลลัพธ์", th_owner:"เจ้าของ",
  th_type:"ประเภท", th_speed:"ความเร็ว", th_gate:"ช่องทาง", th_time:"เวลา", no_data:"ไม่พบข้อมูล",
  search_vehicle:"ค้นหาทะเบียน เจ้าของ บ้านเลขที่", add_vehicle:"เพิ่มรถ",
  th_unit:"บ้านเลขที่", th_model:"รุ่นและสี", th_expiry:"หมดอายุ", th_status:"สถานะ",
  st_active:"ใช้งาน", st_suspended:"ระงับ", no_expiry:"ไม่จำกัด",
  m_add_vehicle:"เพิ่มรถใหม่", m_edit_vehicle:"แก้ไขข้อมูลรถ",
  f_plate:"ทะเบียนรถ", f_owner:"ชื่อเจ้าของ", f_unit:"บ้านเลขที่หรือยูนิต",
  f_type:"ประเภท", f_brand:"รุ่นรถ", f_color:"สี", f_year:"ปี (พ.ศ./ค.ศ.)", f_valid:"วันหมดอายุ", f_status:"สถานะ",
  f_province:"จังหวัด", th_province:"จังหวัด", c_province:"จังหวัด",
  save:"บันทึก", cancel:"ยกเลิก", saved:"บันทึกเรียบร้อย", added:"เพิ่มเรียบร้อย",
  need_plate:"กรุณากรอกทะเบียนรถ",
  bl_note:"รถในบัญชีดำจะถูกปฏิเสธการเข้าโดยอัตโนมัติ และแจ้งเตือนเจ้าหน้าที่ทันที",
  add_to_bl:"เพิ่มทะเบียน", th_reason:"เหตุผล", th_added:"วันที่เพิ่ม",
  m_add_bl:"เพิ่มทะเบียนเข้าบัญชีดำ", f_reason:"เหตุผล",
  r_total:"เหตุการณ์ทั้งหมด", r_registered:"รถที่ลงทะเบียน", r_blacklisted:"ทะเบียนบัญชีดำ",
  chart_title:"การเข้าออก 7 วันล่าสุด", breakdown:"สัดส่วนผลลัพธ์",
  hourly_title:"ช่วงเวลาที่หนาแน่น (24 ชม.)", hourly_sub:"นับจาก 7 วันล่าสุด",
  top_title:"รถที่ผ่านบ่อยที่สุด", top_sub:"30 วันล่าสุด",
  speed_title:"การกระจายความเร็ว", speed_sub:"30 วันล่าสุด · เกณฑ์ ≤ 35 km/h",
  ocr_title:"ความมั่นใจของ OCR", ocr_sub:"30 วันล่าสุด",
  export_title:"ดาวน์โหลดข้อมูล", export_sub:"ส่งออกข้อมูลเหตุการณ์เป็นไฟล์ CSV เพื่อนำไปวิเคราะห์",
  export_from:"ตั้งแต่วันที่", export_to:"ถึงวันที่", export_filter:"กรองตามผล",
  export_all:"ทั้งหมด", export_btn:"ดาวน์โหลด CSV", exporting:"กำลังเตรียมไฟล์",
  th_last_seen:"ครั้งล่าสุด", th_count:"จำนวนครั้ง", over_limit:"เกินเกณฑ์",
  peak_at:"ชั่วโมงที่หนาแน่นสุด",
  set_system:"ข้อมูลระบบ", set_integration:"การเชื่อมต่อภายนอก",
  set_users:"ผู้ใช้งานระบบ", add_user:"เพิ่มผู้ใช้",
  kv_system:"ระบบ", kv_gate:"ช่องทาง", kv_speed:"เกณฑ์ความเร็ว", kv_ocr:"OCR model", kv_user:"ผู้ใช้งานปัจจุบัน",
  kv_rest:"REST API", kv_docs:"เอกสาร API", kv_webhook:"Webhook", webhook_on:"เปิดใช้งาน",
  integration_desc:"ระบบอื่นเชื่อมต่อผ่าน REST API และรับ event แบบเรียลไทม์ผ่าน webhook",
  th_username:"ชื่อผู้ใช้", th_name:"ชื่อและสกุล", th_role:"สิทธิ์", th_created:"สร้างเมื่อ", th_actions:"จัดการ",
  m_add_user:"เพิ่มผู้ใช้งาน", f_name:"ชื่อและสกุล", f_role:"สิทธิ์การใช้งาน",
  confirm_del:"ยืนยันการลบ", del:"ลบ", deleted:"ลบเรียบร้อย",
  q_del_vehicle:"ลบรถคันนี้ออกจากระบบ", q_del_bl:"นำทะเบียนนี้ออกจากบัญชีดำ",
  fill_all:"กรุณากรอกข้อมูลให้ครบ", gate_main:"MAIN 01 ขาเข้า", speed_rule:"ไม่เกิน 35 km/h",
},
en:{
  app_tag:"Access Control", menu:"Menu",
  nav_console:"Dashboard", nav_log:"Access Log", nav_vehicles:"Vehicles",
  nav_blacklist:"Blacklist", nav_reports:"Reports", nav_settings:"Settings",
  sub_console:"Real time entry overview", sub_log:"Complete record of all passages",
  sub_vehicles:"Vehicles registered in the system", sub_blacklist:"Plates blocked from entry",
  sub_reports:"Usage statistics and trends", sub_settings:"Users and integrations",
  role_admin:"Administrator", role_operator:"Operator", logout:"Sign out",
  login_sub:"Access Control System", f_username:"Username", f_password:"Password",
  signin:"Sign in", signing:"Signing in", demo_accounts:"Demo accounts",
  err_cred:"Incorrect username or password", err_conn:"Cannot reach the server",
  d_granted:"Granted", d_denied:"Denied", d_alert:"Review",
  d_granted_full:"Access granted", d_denied_full:"Access denied", d_alert_full:"Unregistered vehicle",
  v_resident:"Resident", v_staff:"Staff", v_visitor:"Visitor",
  s_today:"Today", s_granted:"Granted", s_denied:"Denied", s_alert:"Flagged",
  recent:"Recent Activity", live:"Live",
  welcome:"Welcome", welcome_sub:"Your activity and access summary at a glance",
  live_camera:"Live Camera", not_connected:"Not connected",
  live_cam_msg:"The live camera view will appear here",
  live_cam_note:"Future feature, enabled once an IP camera is connected over RTSP",
  retention_label:"Image retention", retention_val:"90 days",
  pipe_title:"Processing Pipeline",
  pipe_capture:"Camera Feed", pipe_detect:"Plate Detection", pipe_ocr:"OCR Reading",
  pipe_decide:"Access Decision", pipe_log:"Log and API",
  account:"My Account", change_pw:"Change password", m_change_pw:"Change Password",
  f_current_pass:"Current password", f_new_pass:"New password",
  f_confirm_pass:"Confirm new password", pw_mismatch:"New passwords do not match",
  pw_short:"Password must be at least 6 characters", pw_changed:"Password changed",
  m_edit_user:"Edit User", q_del_user:"Remove this user account",
  f_new_pass_optional:"New password (leave blank to keep current)",
  c_owner:"Owner", c_type:"Type", c_speed:"Speed", c_conf:"OCR confidence", c_time:"Time",
  c_color:"Color", c_brand:"Make / Model", c_year:"Year",
  connecting:"Connecting", connected:"Streaming", demo_preview:"Demo preview",
  unknown:"Unknown", no_events:"No activity yet", no_image:"No image",
  open_gate:"Open Barrier", approve:"Approve Manually",
  gate_opened:"Barrier opened (simulated)", approved:"Approved", unregistered:"Unregistered vehicle",
  search_plate:"Search plate", all_results:"All results", refresh:"Refresh", load_more:"Load more",
  th_image:"Image", th_plate:"Plate", th_result:"Result", th_owner:"Owner",
  th_type:"Type", th_speed:"Speed", th_gate:"Gate", th_time:"Time", no_data:"No results found",
  search_vehicle:"Search plate, owner or unit", add_vehicle:"Add Vehicle",
  th_unit:"Unit", th_model:"Model and Colour", th_expiry:"Expiry", th_status:"Status",
  st_active:"Active", st_suspended:"Suspended", no_expiry:"No expiry",
  m_add_vehicle:"Add Vehicle", m_edit_vehicle:"Edit Vehicle",
  f_plate:"Plate number", f_owner:"Owner name", f_unit:"Unit or address",
  f_type:"Type", f_brand:"Make / Model", f_color:"Colour", f_year:"Year", f_valid:"Valid until", f_status:"Status",
  f_province:"Province", th_province:"Province", c_province:"Province",
  save:"Save", cancel:"Cancel", saved:"Saved", added:"Added",
  need_plate:"Please enter a plate number",
  bl_note:"Blacklisted vehicles are denied entry automatically and staff are alerted.",
  add_to_bl:"Add Plate", th_reason:"Reason", th_added:"Date added",
  m_add_bl:"Add Plate to Blacklist", f_reason:"Reason",
  r_total:"Total Events", r_registered:"Registered Vehicles", r_blacklisted:"Blacklisted",
  chart_title:"Activity over the last 7 days", breakdown:"Outcome breakdown",
  hourly_title:"Peak hours (24h)", hourly_sub:"Last 7 days",
  top_title:"Most frequent vehicles", top_sub:"Last 30 days",
  speed_title:"Speed distribution", speed_sub:"Last 30 days · limit ≤ 35 km/h",
  ocr_title:"OCR confidence", ocr_sub:"Last 30 days",
  export_title:"Export data", export_sub:"Download access events as a CSV file for further analysis",
  export_from:"From date", export_to:"To date", export_filter:"Filter by decision",
  export_all:"All", export_btn:"Download CSV", exporting:"Preparing file",
  th_last_seen:"Last seen", th_count:"Visits", over_limit:"Over limit",
  peak_at:"Peak at",
  set_system:"System Information", set_integration:"Integrations",
  set_users:"System Users", add_user:"Add User",
  kv_system:"System", kv_gate:"Gate", kv_speed:"Speed limit", kv_ocr:"OCR model", kv_user:"Current user",
  kv_rest:"REST API", kv_docs:"API docs", kv_webhook:"Webhook", webhook_on:"Enabled",
  integration_desc:"External systems connect via the REST API and receive real time events through webhooks.",
  th_username:"Username", th_name:"Full name", th_role:"Role", th_created:"Created", th_actions:"Actions",
  m_add_user:"Add User", f_name:"Full name", f_role:"Access role",
  confirm_del:"Confirm deletion", del:"Delete", deleted:"Deleted",
  q_del_vehicle:"Remove this vehicle from the system", q_del_bl:"Remove this plate from the blacklist",
  fill_all:"Please fill in all fields", gate_main:"MAIN 01 Entry", speed_rule:"Up to 35 km/h",
},
};
let LANG = localStorage.getItem("alpr_lang") || "en";
const t = k => (STR[LANG] && STR[LANG][k]) || k;

/* ---------- theme ---------- */
const getTheme = () => document.documentElement.getAttribute("data-theme") || "light";
function setTheme(mode){
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem("alpr_theme", mode);
  const b = $("#theme-btn"); if(b) b.innerHTML = icon(mode==="dark"?"sun":"moon",16);
}

/* ---------- helpers ---------- */
const $  = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const esc = s => String(s==null?"":s).replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const debounce = (fn,ms)=>{ let x; return (...a)=>{ clearTimeout(x); x=setTimeout(()=>fn(...a),ms); }; };
const capName = p => p ? p.split(/[\\/]/).pop() : "";
const blank = '<span class="t-mute">·</span>';
function fmtTime(ts){
  if(!ts) return "·";
  const d = new Date(String(ts).replace(" ","T"));
  if(isNaN(d)) return ts;
  return d.toLocaleString(LANG==="th"?"th-TH":"en-GB",
    {day:"2-digit",month:"short",hour:"2-digit",minute:"2-digit"});
}
function fmtClockShort(ts){
  const d = new Date(String(ts).replace(" ","T"));
  return isNaN(d) ? ts : d.toLocaleTimeString(LANG==="th"?"th-TH":"en-GB",
    {hour:"2-digit",minute:"2-digit",second:"2-digit"});
}
const decClass = {granted:"badge-granted",denied:"badge-denied",alert:"badge-alert"};
const decBadge = d => `<span class="badge ${decClass[d]||"badge-soft"}">${t("d_"+d)||d}</span>`;
const vtypeClass = {resident:"badge-resident",staff:"badge-staff",visitor:"badge-visitor"};
const vtypeBadge = v => v
  ? `<span class="badge ${vtypeClass[v]||"badge-soft"}">${t("v_"+v)||v}</span>` : blank;
const emptyRow = c => `<tr><td colspan="${c}"><div class="empty">${icon("search",34)}<div>${t("no_data")}</div></div></td></tr>`;

/* ---------- API ---------- */
const API = {
  token: localStorage.getItem("alpr_token") || null,
  async req(method, path, body){
    const opt = { method, headers:{} };
    if(this.token) opt.headers["Authorization"] = "Bearer "+this.token;
    if(body!==undefined){ opt.headers["Content-Type"]="application/json"; opt.body=JSON.stringify(body); }
    const res = await fetch(path, opt);
    if(res.status===401){ this.token=null; localStorage.removeItem("alpr_token"); renderLogin(); throw new Error("unauthorized"); }
    if(!res.ok){ let m=res.statusText; try{ m=(await res.json()).detail||m; }catch(e){} throw new Error(m); }
    return res.status===204 ? null : res.json();
  },
  get(p){return this.req("GET",p);}, post(p,b){return this.req("POST",p,b);},
  put(p,b){return this.req("PUT",p,b);}, patch(p,b){return this.req("PATCH",p,b);},
  del(p){return this.req("DELETE",p);},
};
const State = { user:null, view:"console", timer:null, lastEventId:0 };
let clockTimer = null;

/* ---------- toast & modal ---------- */
function toast(msg, type="info"){
  const el = document.createElement("div");
  el.className = "toast "+type;
  el.innerHTML = icon(type==="success"?"check":type==="error"?"x":"alert",16)+`<span>${esc(msg)}</span>`;
  $("#toast-root").appendChild(el);
  setTimeout(()=>{ el.style.transition="opacity .3s"; el.style.opacity="0"; setTimeout(()=>el.remove(),300); }, 3200);
}
function modal({title, body, submitLabel, submitClass="btn-primary", onSubmit}){
  const root = $("#modal-root");
  root.innerHTML = `<div class="modal-overlay"><div class="modal">
    <div class="modal-head"><div class="modal-title">${esc(title)}</div>
      <button class="icon-btn" data-close>${icon("x",16)}</button></div>
    <div class="modal-body">${body}</div>
    <div class="modal-foot">
      <button class="btn btn-ghost" data-close>${t("cancel")}</button>
      <button class="btn ${submitClass}" data-submit>${esc(submitLabel||t("save"))}</button>
    </div></div></div>`;
  const close = ()=>{ root.innerHTML=""; };
  root.querySelectorAll("[data-close]").forEach(b=>b.onclick=close);
  root.querySelector(".modal-overlay").onclick = e=>{ if(e.target.classList.contains("modal-overlay")) close(); };
  root.querySelector("[data-submit]").onclick = async ()=>{
    try{ await onSubmit(close); }catch(e){ toast(e.message,"error"); }
  };
}
function confirmDel(url, msg, reload){
  modal({ title:t("confirm_del"), submitLabel:t("del"), submitClass:"btn-danger",
    body:`<p style="color:var(--text-2)">${esc(msg)}</p>`,
    onSubmit: async close=>{ await API.del(url); close(); toast(t("deleted"),"success"); reload(); } });
}

/* event detail popup -- enlarged capture image beside the recognised data,
   so a reviewer can confirm the read against the actual photo */
function eventPopup(ev){
  const img = capName(ev.image_path);
  // Always show the same capture image the user clicked on, just larger.
  // Showing a wide shot here would duplicate Live Camera, which is confusing.
  const imgUrl = img ? "/api/captures/" + img : null;
  const txt = {granted:t("d_granted_full"),denied:t("d_denied_full"),
               alert:t("d_alert_full")}[ev.decision]||ev.decision;
  const ic = ev.decision==="granted"?"check":ev.decision==="denied"?"ban":"alert";
  const root = $("#modal-root");
  root.innerHTML = `<div class="modal-overlay"><div class="modal modal-wide">
    <div class="modal-head"><div class="modal-title">${t("th_plate")} · ${esc(ev.plate)}</div>
      <button class="icon-btn" data-close>${icon("x",16)}</button></div>
    <div class="modal-body">
      <div class="lb-img">${imgUrl
        ? `<img src="${imgUrl}">`
        : `<span class="nocap">${t("no_image")}</span>`}</div>
      <div class="decision-banner ${ev.decision}">${icon(ic,21)}
        <div><div class="db-main">${txt}</div><div class="db-sub">${esc(ev.reason||"")}</div></div></div>
      <div class="hero-info" style="margin:14px 0 0">
        <div class="info-row"><span class="k">${t("c_owner")}</span><span class="v">${esc(ev.owner_name||t("unknown"))}</span></div>
        ${ev.province?`<div class="info-row"><span class="k">${t("c_province")}</span><span class="v">${esc(ev.province)}</span></div>`:""}
        <div class="info-row"><span class="k">${t("c_type")}</span><span class="v">${vtypeBadge(ev.vehicle_type)}</span></div>
        ${ev.brand_model?`<div class="info-row"><span class="k">${t("c_brand")}</span><span class="v">${esc(ev.brand_model)}</span></div>`:""}
        ${ev.vehicle_color?`<div class="info-row"><span class="k">${t("c_color")}</span><span class="v">${esc(ev.vehicle_color)}</span></div>`:""}
        ${ev.vehicle_year?`<div class="info-row"><span class="k">${t("c_year")}</span><span class="v">${ev.vehicle_year}</span></div>`:""}
        <div class="info-row"><span class="k">${t("c_speed")}</span><span class="v">${(ev.speed_kmh??0).toFixed(1)} km/h</span></div>
        <div class="info-row"><span class="k">${t("c_conf")}</span><span class="v">${((ev.confidence??0)*100).toFixed(1)}%</span></div>
        <div class="info-row"><span class="k">${t("th_gate")}</span><span class="v">${esc(ev.gate||"·")}</span></div>
        <div class="info-row"><span class="k">${t("c_time")}</span><span class="v">${fmtTime(ev.timestamp)}</span></div>
      </div>
    </div></div></div>`;
  const close = ()=>{ root.innerHTML=""; };
  root.querySelectorAll("[data-close]").forEach(b=>b.onclick=close);
  root.querySelector(".modal-overlay").onclick = e=>{
    if(e.target.classList.contains("modal-overlay")) close(); };
}

/* ---------- shared controls ---------- */
function controls(){
  return `<div class="seg" id="lang-seg">
      <button data-lang="th" class="${LANG==="th"?"on":""}">TH</button>
      <button data-lang="en" class="${LANG==="en"?"on":""}">EN</button>
    </div>
    <button class="icon-btn" id="theme-btn">${icon(getTheme()==="dark"?"sun":"moon",16)}</button>`;
}
function wireControls(afterLang){
  $$("#lang-seg [data-lang]").forEach(b=>b.onclick=()=>{
    if(b.dataset.lang===LANG) return;
    LANG = b.dataset.lang; localStorage.setItem("alpr_lang", LANG);
    document.documentElement.lang = LANG;
    afterLang();
  });
  const tb = $("#theme-btn");
  if(tb) tb.onclick = ()=> setTheme(getTheme()==="dark"?"light":"dark");
}

/* ---------- login ---------- */
/* the login page is always English and carries no theme / language switch */
function renderLogin(err){
  $("#app").innerHTML = `<div class="login-wrap">
    <div class="login-aside">
      <div class="la-wordmark">
        <img class="la-logo" src="/img/deepalpr.png" alt="Deep ALPR">
        <div class="wm-name">Deep ALPR</div>
        <div class="wm-tag">ACCESS CONTROL SYSTEM</div>
      </div>
    </div>
    <div class="login-main">
      <div class="login-form">
        <div class="lf-brand">
          <img class="lf-mark" src="/img/deepalpr.png" alt="Deep ALPR">
          <div><div class="lf-name">Deep ALPR</div><div class="lf-tag">Access Control System</div></div>
        </div>
        <h2>Sign in</h2>
        <div class="lf-sub">Welcome back. Please enter your details.</div>
        <div class="field"><label>Username</label><input class="input" id="lg-user" placeholder="username"></div>
        <div class="field"><label>Password</label><input class="input" id="lg-pass" type="password" placeholder="••••••••"></div>
        <button class="btn btn-primary btn-block" id="lg-btn" style="margin-top:6px">Sign in</button>
        ${err?`<div class="login-err">${esc(err)}</div>`:""}
        <div class="login-hint">Demo accounts &nbsp; admin / admin123 &nbsp; · &nbsp; operator / operator123</div>
      </div>
    </div>
  </div>`;
  const submit = async ()=>{
    const u=$("#lg-user").value.trim(), p=$("#lg-pass").value;
    if(!u||!p) return;
    $("#lg-btn").textContent = "Signing in";
    try{
      const r = await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({username:u,password:p})});
      if(!r.ok){ const e=await r.json().catch(()=>({})); return renderLogin(e.detail||"Incorrect username or password"); }
      const data = await r.json();
      API.token = data.token; localStorage.setItem("alpr_token",data.token);
      State.user = data.user; renderApp("console");
    }catch(e){ renderLogin("Cannot reach the server"); }
  };
  $("#lg-btn").onclick = submit;
  $("#lg-pass").onkeydown = e=>{ if(e.key==="Enter") submit(); };
  $("#lg-user").focus();
}

/* ---------- shell ---------- */
const NAV = [
  {id:"console",  ic:"grid"},
  {id:"log",      ic:"list"},
  {id:"vehicles", ic:"car"},
  {id:"blacklist",ic:"ban"},
  {id:"reports",  ic:"chart"},
  {id:"settings", ic:"settings"},
];
function setSidebar(open){
  const sb = $(".sidebar"), bd = $("#sb-backdrop");
  if(sb) sb.classList.toggle("open", open);
  if(bd) bd.classList.toggle("show", open);
}
function renderApp(view){
  const u = State.user;
  const initial = (u.display_name||u.username||"?").trim().charAt(0).toUpperCase();
  $("#app").innerHTML = `<div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <img class="brand-mark" src="/img/deepalpr.png" alt="Deep ALPR">
        <div><div class="brand-name">Deep ALPR</div><div class="brand-tag">${t("app_tag")}</div></div>
      </div>
      <nav class="nav">
        <div class="nav-label">${t("menu")}</div>
        ${NAV.map(n=>`<a class="nav-item" data-nav="${n.id}">${icon(n.ic,17)}<span>${t("nav_"+n.id)}</span></a>`).join("")}
      </nav>
      <div class="user-card">
        <div class="avatar">${initial}</div>
        <div class="user-meta"><div class="user-name">${esc(u.display_name||u.username)}</div>
          <div class="user-role">${u.role==="admin"?t("role_admin"):t("role_operator")}</div></div>
        <button class="icon-btn" id="logout-btn" title="${t("logout")}">${icon("logout",16)}</button>
      </div>
    </aside>
    <div class="sidebar-backdrop" id="sb-backdrop"></div>
    <main class="main">
      <header class="topbar">
        <div class="topbar-left">
          <button class="icon-btn menu-btn" id="menu-btn">${icon("menu",18)}</button>
          <div><div class="page-title" id="pg-title"></div><div class="page-sub" id="pg-sub"></div></div>
        </div>
        <div class="topbar-right">
          ${controls()}
          <span class="clock" id="clock"></span>
          <span class="live-dot">${t("live").toUpperCase()}</span>
        </div>
      </header>
      <div class="content" id="content"><div class="spinner"></div></div>
    </main>
  </div>`;
  $$("[data-nav]").forEach(a=>a.onclick=()=>{ navigate(a.dataset.nav); setSidebar(false); });
  $("#logout-btn").onclick = logout;
  $("#menu-btn").onclick = ()=> setSidebar(!$(".sidebar").classList.contains("open"));
  $("#sb-backdrop").onclick = ()=> setSidebar(false);
  wireControls(()=>renderApp(State.view));
  if(clockTimer) clearInterval(clockTimer);
  const tick=()=>{ const c=$("#clock"); if(c) c.textContent=new Date().toLocaleTimeString(LANG==="th"?"th-TH":"en-GB"); };
  tick(); clockTimer = setInterval(tick,1000);
  navigate(view);
}
function navigate(view){
  State.view = view;
  if(State.timer){ clearInterval(State.timer); State.timer=null; }
  if(State.liveTimer){ clearInterval(State.liveTimer); State.liveTimer=null; }
  $$("[data-nav]").forEach(a=>a.classList.toggle("active", a.dataset.nav===view));
  $("#pg-title").textContent = t("nav_"+view);
  $("#pg-sub").textContent = t("sub_"+view);
  $("#content").innerHTML = '<div class="spinner"></div>';
  VIEWS[view]().catch(e=>{ if(e.message!=="unauthorized")
    $("#content").innerHTML = `<div class="empty">${icon("alert",34)}<div>${esc(e.message)}</div></div>`; });
}
async function logout(){
  try{ await API.post("/api/auth/logout"); }catch(e){}
  API.token=null; localStorage.removeItem("alpr_token"); State.user=null;
  if(State.timer) clearInterval(State.timer);
  if(State.liveTimer) clearInterval(State.liveTimer);
  if(clockTimer) clearInterval(clockTimer);
  renderLogin();
}

/* ---------- view: console ---------- */
function statCard(label,val,ic,tone){
  return `<div class="stat"><div class="stat-top"><span class="stat-label">${label}</span>
    <span class="stat-ico tone-${tone}">${icon(ic,16)}</span></div>
    <div class="stat-val">${val??0}</div></div>`;
}
function statGrid(s){
  return statCard(t("s_today"),s.today_events,"car","ink")
       + statCard(t("s_granted"),s.granted,"check","granted")
       + statCard(t("s_denied"),s.denied,"ban","denied")
       + statCard(t("s_alert"),s.alert,"alert","alert");
}
function pipelineCard(){
  const steps = [
    {ic:"video", k:"pipe_capture"},
    {ic:"plate", k:"pipe_detect"},
    {ic:"scan",  k:"pipe_ocr"},
    {ic:"check", k:"pipe_decide"},
    {ic:"send",  k:"pipe_log"},
  ];
  const inner = steps.map((s,i)=>
    `<div class="pipe-step"><div class="ps-ico">${icon(s.ic,21)}</div>`
    + `<div class="ps-label">${t(s.k)}</div></div>`
    + (i < steps.length-1 ? '<div class="pipe-arrow"></div>' : "")
  ).join("");
  return `<div class="card pipeline section-gap">
    <div class="card-head">
      <div class="card-title">${t("pipe_title")}</div>
      <span class="live-dot">${t("live")}</span>
    </div>
    <div class="pipe-flow">${inner}</div>
  </div>`;
}
async function viewConsole(){
  const [stats, events] = await Promise.all([API.get("/api/stats"), API.get("/api/events?limit=13")]);
  const who = esc(State.user.display_name||State.user.username);
  $("#content").innerHTML = `
    <div class="welcome">
      <h2>${t("welcome")}, <span class="nm">${who}</span></h2>
      <p>${t("welcome_sub")}</p>
    </div>
    <div class="grid grid-4" id="stat-grid">${statGrid(stats)}</div>
    ${pipelineCard()}
    <div class="card live-cam">
      <div class="card-head">
        <div class="card-title">${t("live_camera")}</div>
        <span class="badge badge-soft" id="lc-status">${icon("pin",12)} MAIN 01 &nbsp;·&nbsp; ${t("connecting")}</span>
      </div>
      <div class="live-cam-frame" id="lc-frame">
        <img id="lc-img" alt="Live preview" style="display:none">
        <div class="live-cam-ph" id="lc-empty">
          ${icon("video",38)}
          <div class="lcp-title">${t("live_cam_msg")}</div>
          <div class="lcp-note">${t("live_cam_note")}</div>
        </div>
        <div class="live-overlay" id="lc-overlay"></div>
      </div>
    </div>
    <div class="console-grid">
      <div class="live-hero" id="hero"></div>
      <div class="feed">
        <div class="feed-head"><div class="card-title">${t("recent")}</div><span class="live-dot">${t("live")}</span></div>
        <div class="feed-list" id="feed"></div>
      </div>
    </div>`;
  // Demo mode: anchor every "now" view on the Live Camera car so MAIN 01,
  // Live Camera, and the top of Recent Activity all stay in sync.
  const feedEvents = [LIVE_DEMO.event, ...events];
  renderHero(LIVE_DEMO.event);
  renderFeed(feedEvents);
  State.lastEventId = events.length ? events[0].id : 0;
  State.timer = setInterval(pollConsole, 3000);
  startLiveCamera();
}

/* ---------- Live Camera (static demo image + frozen overlay) ----------
 * Demo mode shows a fixed photo of a real Thai vehicle. The overlay card
 * shows the AI-extracted details for THAT specific car -- not a rolling
 * feed from the DB -- so the demo is repeatable and predictable.
 *
 * When the customer wires up real CCTV, swap the <img src> for the camera's
 * MJPEG endpoint and replace the LIVE_DEMO object below with the polling
 * logic. */
const LIVE_DEMO = {
  image: "/img/honda_jazz.png?v=20260523i",
  // Frozen event payload. This single object is what Live Camera, the MAIN 01
  // hero card, and the top of Recent Activity all render so the three views
  // stay consistent in demo mode.
  event: {
    id: -1,
    decision: "granted",
    reason: "Registered resident",
    plate: "กร5539",
    owner_name: "สุดารัตน์ ทองคำ",
    province: "พระนครศรีอยุธยา",
    vehicle_color: "ขาว",
    vehicle_type: "resident",
    brand_model: "Honda Jazz",
    vehicle_year: 2014,
    speed_kmh: 8.4,
    confidence: 0.998,
    gate: "MAIN 01",
    image_path: "demo_honda_jazz_plate.png",          // close-up of the plate
    timestamp: new Date().toISOString(),
  },
};

function startLiveCamera(){
  if(State.liveTimer) clearInterval(State.liveTimer);   // no polling in demo mode
  const img = $("#lc-img"), empty = $("#lc-empty");
  const overlay = $("#lc-overlay"), status = $("#lc-status");
  if(!img) return;

  img.onload  = ()=>{ if(empty) empty.style.display = "none"; img.style.display = "block"; };
  img.onerror = ()=>{ img.style.display = "none"; if(empty) empty.style.display = "flex"; };
  img.src = LIVE_DEMO.image;

  if(status) status.innerHTML =
    `${icon("pin",12)} MAIN 01 &nbsp;·&nbsp; <span style="color:var(--accent);font-weight:700">${t("demo_preview")}</span>`;

  renderLiveOverlay(overlay, LIVE_DEMO.event);
  // Keep the overlay visible (renderLiveOverlay normally auto-hides after 8s)
  overlay.classList.add("lo-show");
  clearTimeout(overlay._fadeTimer);
}

function renderLiveOverlay(el, ev){
  if(!el) return;
  const dec = ev.decision || "alert";
  const txt = {granted:t("d_granted_full"),denied:t("d_denied_full"),alert:t("d_alert_full")}[dec]||dec;
  const ic  = dec==="granted"?"check":dec==="denied"?"ban":"alert";
  const parts = [
    `<span class="lo-row"><span class="lo-k">${t("c_owner")}</span> ${esc(ev.owner_name||t("unknown"))}</span>`,
    ev.province      ? `<span class="lo-row"><span class="lo-k">${t("c_province")}</span> ${esc(ev.province)}</span>` : "",
    ev.vehicle_color ? `<span class="lo-row"><span class="lo-k">${t("c_color")}</span> ${esc(ev.vehicle_color)}</span>` : "",
    ev.brand_model   ? `<span class="lo-row"><span class="lo-k">${t("c_brand")}</span> ${esc(ev.brand_model)}</span>` : "",
    ev.vehicle_year  ? `<span class="lo-row"><span class="lo-k">${t("c_year")}</span> ${ev.vehicle_year}</span>` : "",
    `<span class="lo-row"><span class="lo-k">${t("c_speed")}</span> ${(ev.speed_kmh??0).toFixed(1)} km/h</span>`,
  ].filter(Boolean).join("");
  el.innerHTML = `
    <div class="lo-card lo-${dec}">
      <div class="lo-banner">${icon(ic,18)} <span>${txt}</span></div>
      <div class="lo-plate">${esc(ev.plate||"")}</div>
      <div class="lo-rows">${parts}</div>
    </div>`;
  el.classList.add("lo-show");
  clearTimeout(el._fadeTimer);
  el._fadeTimer = setTimeout(()=>el.classList.remove("lo-show"), 8000);
}
function renderHero(ev){
  const h = $("#hero"); if(!h) return;
  if(!ev){ h.innerHTML = `<div class="empty" style="padding:90px 20px">${icon("car",38)}<div>${t("no_events")}</div></div>`; return; }
  const img = capName(ev.image_path);
  const txt = {granted:t("d_granted_full"),denied:t("d_denied_full"),alert:t("d_alert_full")}[ev.decision]||ev.decision;
  const ic  = ev.decision==="granted"?"check":ev.decision==="denied"?"ban":"alert";
  h.innerHTML = `
    <div class="hero-cap">
      ${img?`<img class="zoomable" data-ev="${ev.id}" src="/api/captures/${img}" onerror="this.style.display='none';this.nextElementSibling.style.display='block'">`:""}
      <span class="nocap" ${img?'style="display:none"':""}>${t("no_image")}</span>
      <div class="hero-deco"><span class="badge badge-soft">${icon("pin",12)} ${esc(ev.gate||"GATE")}</span></div>
    </div>
    <div class="hero-body">
      <div class="decision-banner ${ev.decision}">${icon(ic,20)}
        <div><div class="db-main">${txt}</div><div class="db-sub">${esc(ev.reason||"")}</div></div></div>
      <div style="text-align:center;margin:2px 0 6px"><span class="plate-tag xl">${esc(ev.plate)}</span></div>
      <div class="hero-info">
        <div class="info-row"><span class="k">${t("c_owner")}</span><span class="v">${esc(ev.owner_name||t("unknown"))}</span></div>
        ${ev.province?`<div class="info-row"><span class="k">${t("c_province")}</span><span class="v">${esc(ev.province)}</span></div>`:""}
        <div class="info-row"><span class="k">${t("c_type")}</span><span class="v">${vtypeBadge(ev.vehicle_type)}</span></div>
        ${ev.brand_model?`<div class="info-row"><span class="k">${t("c_brand")}</span><span class="v">${esc(ev.brand_model)}</span></div>`:""}
        ${ev.vehicle_color?`<div class="info-row"><span class="k">${t("c_color")}</span><span class="v">${esc(ev.vehicle_color)}</span></div>`:""}
        ${ev.vehicle_year?`<div class="info-row"><span class="k">${t("c_year")}</span><span class="v">${ev.vehicle_year}</span></div>`:""}
        <div class="info-row"><span class="k">${t("c_speed")}</span><span class="v">${(ev.speed_kmh??0).toFixed(1)} km/h</span></div>
        <div class="info-row"><span class="k">${t("c_conf")}</span><span class="v">${((ev.confidence??0)*100).toFixed(1)}%</span></div>
        <div class="info-row"><span class="k">${t("c_time")}</span><span class="v">${fmtTime(ev.timestamp)}</span></div>
      </div>
      <div class="hero-actions">
        <button class="btn" id="hero-open">${icon("gate",15)} ${t("open_gate")}</button>
        ${ev.decision==="alert"?`<button class="btn btn-primary" id="hero-grant">${icon("check",15)} ${t("approve")}</button>`:""}
      </div>
    </div>`;
  $("#hero-open").onclick = async ()=>{
    try{ await API.post("/api/gate/open",{plate:ev.plate}); toast(t("gate_opened"),"success"); }
    catch(e){ toast(e.message,"error"); }
  };
  const g = $("#hero-grant");
  if(g) g.onclick = async ()=>{
    try{ await API.patch("/api/events/"+ev.id,{decision:"granted"}); toast(t("approved"),"success"); navigate("console"); }
    catch(e){ toast(e.message,"error"); }
  };
}
function renderFeed(events, newIds){
  const f = $("#feed"); if(!f) return;
  if(!events.length){ f.innerHTML = `<div class="empty">${icon("list",36)}<div>${t("no_events")}</div></div>`; return; }
  f.innerHTML = events.map(ev=>{
    const img = capName(ev.image_path);
    const provBit = ev.province ? `<span class="feed-prov">${esc(ev.province)}</span>` : "";
    return `<div class="feed-item ${newIds&&newIds.has(ev.id)?"new":""}">
      ${img?`<img class="feed-thumb zoomable" data-ev="${ev.id}" src="/api/captures/${img}" onerror="this.style.visibility='hidden'">`:'<div class="feed-thumb"></div>'}
      <div class="feed-mid">
        <div class="feed-plate">${esc(ev.plate)} ${provBit}</div>
        <div class="feed-meta">${esc(ev.owner_name||t("unregistered"))} &nbsp;·&nbsp; ${fmtClockShort(ev.timestamp)}</div></div>
      ${decBadge(ev.decision)}</div>`;
  }).join("");
}
async function pollConsole(){
  if(State.view!=="console") return;
  try{
    const events = await API.get("/api/events?limit=13");
    if(!events.length) return;
    let newIds = null;
    if(events[0].id !== State.lastEventId){
      newIds = new Set(events.filter(e=>e.id>State.lastEventId).map(e=>e.id));
      State.lastEventId = events[0].id;
      // MAIN 01 hero stays pinned to the Live Camera demo car (see viewConsole).
      API.get("/api/stats").then(s=>{ const g=$("#stat-grid"); if(g) g.innerHTML=statGrid(s); }).catch(()=>{});
    }
    renderFeed([LIVE_DEMO.event, ...events], newIds);
  }catch(e){}
}

/* ---------- view: access log ---------- */
async function viewLog(){
  $("#content").innerHTML = `
    <div class="toolbar">
      <div class="search">${icon("search",15)}<input id="lg-q" placeholder="${t("search_plate")}"></div>
      <select class="select" id="lg-dec" style="max-width:170px">
        <option value="">${t("all_results")}</option>
        <option value="granted">${t("d_granted")}</option>
        <option value="denied">${t("d_denied")}</option>
        <option value="alert">${t("d_alert")}</option>
      </select>
      <button class="btn btn-ghost" id="lg-refresh">${icon("refresh",15)} ${t("refresh")}</button>
    </div>
    <div class="card"><div class="tbl-wrap"><table>
      <thead><tr><th>${t("th_image")}</th><th>${t("th_plate")}</th><th>${t("th_result")}</th>
        <th>${t("th_owner")}</th><th>${t("th_type")}</th><th>${t("th_speed")}</th>
        <th>${t("th_gate")}</th><th>${t("th_time")}</th></tr></thead>
      <tbody id="lg-body"></tbody></table></div>
      <div style="padding:13px;text-align:center"><button class="btn btn-ghost" id="lg-more">${t("load_more")}</button></div>
    </div>`;
  let offset = 0;
  const load = async append=>{
    const qs = new URLSearchParams({limit:"30",offset:String(offset)});
    const q=$("#lg-q").value.trim(), d=$("#lg-dec").value;
    if(q) qs.set("plate",q);
    if(d) qs.set("decision",d);
    const rows = await API.get("/api/events?"+qs).catch(()=>[]);
    const html = rows.map(rowLog).join("");
    const body = $("#lg-body");
    if(append) body.insertAdjacentHTML("beforeend",html);
    else body.innerHTML = html || emptyRow(8);
    $("#lg-more").style.display = rows.length<30 ? "none" : "";
  };
  const reload = ()=>{ offset=0; load(false); };
  $("#lg-q").oninput = debounce(reload,300);
  $("#lg-dec").onchange = reload;
  $("#lg-refresh").onclick = reload;
  $("#lg-more").onclick = ()=>{ offset+=30; load(true); };
  await load(false);
}
function rowLog(ev){
  const img = capName(ev.image_path);
  return `<tr>
    <td>${img?`<img class="feed-thumb zoomable" data-ev="${ev.id}" src="/api/captures/${img}" onerror="this.style.visibility='hidden'">`:'<div class="feed-thumb"></div>'}</td>
    <td><span class="t-plate">${esc(ev.plate)}</span></td>
    <td>${decBadge(ev.decision)}</td>
    <td>${ev.owner_name?esc(ev.owner_name):blank}</td>
    <td>${vtypeBadge(ev.vehicle_type)}</td>
    <td>${(ev.speed_kmh??0).toFixed(1)} km/h</td>
    <td class="t-mute">${esc(ev.gate||"·")}</td>
    <td class="t-mute">${fmtTime(ev.timestamp)}</td></tr>`;
}

/* ---------- view: vehicles ---------- */
async function viewVehicles(){
  const admin = State.user.role==="admin";
  $("#content").innerHTML = `
    <div class="toolbar">
      <div class="search">${icon("search",15)}<input id="v-q" placeholder="${t("search_vehicle")}"></div>
      <div class="spacer"></div>
      ${admin?`<button class="btn btn-primary" id="v-add">${icon("plus",15)} ${t("add_vehicle")}</button>`:""}
    </div>
    <div class="card"><div class="tbl-wrap"><table>
      <thead><tr><th>${t("th_plate")}</th><th>${t("th_province")}</th>
        <th>${t("th_owner")}</th><th>${t("th_unit")}</th>
        <th>${t("th_type")}</th><th>${t("th_model")}</th><th>${t("th_expiry")}</th>
        <th>${t("th_status")}</th>${admin?"<th></th>":""}</tr></thead>
      <tbody id="v-body"></tbody></table></div></div>`;
  const load = async ()=>{
    const q = $("#v-q").value.trim();
    const rows = await API.get("/api/vehicles"+(q?"?search="+encodeURIComponent(q):"")).catch(()=>[]);
    $("#v-body").innerHTML = rows.map(v=>rowVehicle(v,admin)).join("") || emptyRow(admin?9:8);
    if(admin){
      $$("[data-edit]").forEach(b=>b.onclick=()=>vehicleModal(JSON.parse(b.dataset.edit),load));
      $$("[data-del]").forEach(b=>b.onclick=()=>confirmDel("/api/vehicles/"+b.dataset.del,t("q_del_vehicle"),load));
    }
  };
  $("#v-q").oninput = debounce(load,300);
  if(admin) $("#v-add").onclick = ()=>vehicleModal(null,load);
  await load();
}
function rowVehicle(v,admin){
  return `<tr>
    <td><span class="t-plate">${esc(v.plate)}</span></td>
    <td>${esc(v.province||"·")}</td>
    <td>${esc(v.owner_name||"·")}</td>
    <td>${esc(v.unit||"·")}</td>
    <td>${vtypeBadge(v.vehicle_type)}</td>
    <td>${esc(v.brand_model||"·")}${v.vehicle_year?" "+v.vehicle_year:""}${v.color?" · "+esc(v.color):""}</td>
    <td class="t-mute">${v.valid_until?esc(v.valid_until):t("no_expiry")}</td>
    <td><span class="badge ${v.status==="active"?"badge-granted":"badge-soft"}">${v.status==="active"?t("st_active"):t("st_suspended")}</span></td>
    ${admin?`<td><div class="t-actions">
      <button class="icon-btn" data-edit="${esc(JSON.stringify(v))}">${icon("edit",14)}</button>
      <button class="icon-btn" data-del="${v.id}">${icon("trash",14)}</button></div></td>`:""}
  </tr>`;
}
function vehicleModal(v,reload){
  const e = v||{};
  modal({
    title: v?t("m_edit_vehicle"):t("m_add_vehicle"),
    body:`
      <div class="field-row">
        <div class="field"><label>${t("f_plate")} *</label><input class="input" id="f-plate" value="${esc(e.plate||"")}" placeholder="1กข1234"></div>
        <div class="field"><label>${t("f_province")}</label><input class="input" id="f-province" value="${esc(e.province||"")}" placeholder="กรุงเทพมหานคร"></div>
      </div>
      <div class="field"><label>${t("f_owner")}</label><input class="input" id="f-owner" value="${esc(e.owner_name||"")}"></div>
      <div class="field-row">
        <div class="field"><label>${t("f_unit")}</label><input class="input" id="f-unit" value="${esc(e.unit||"")}"></div>
        <div class="field"><label>${t("f_type")}</label><select class="select" id="f-type">
          ${["resident","staff","visitor"].map(x=>`<option value="${x}" ${e.vehicle_type===x?"selected":""}>${t("v_"+x)}</option>`).join("")}
        </select></div>
      </div>
      <div class="field-row">
        <div class="field"><label>${t("f_brand")}</label><input class="input" id="f-brand" value="${esc(e.brand_model||"")}" placeholder="Toyota Vios"></div>
        <div class="field"><label>${t("f_year")}</label><input class="input" id="f-year" type="number" min="1980" max="2099" value="${e.vehicle_year||""}" placeholder="2024"></div>
      </div>
      <div class="field-row">
        <div class="field"><label>${t("f_color")}</label><input class="input" id="f-color" value="${esc(e.color||"")}" placeholder="ขาว"></div>
        <div class="field"><label>${t("f_valid")}</label><input class="input" id="f-valid" type="date" value="${esc(e.valid_until||"")}"></div>
      </div>
      <div class="field">
        <label>${t("f_status")}</label>
        <select class="select" id="f-status">
          <option value="active" ${e.status!=="suspended"?"selected":""}>${t("st_active")}</option>
          <option value="suspended" ${e.status==="suspended"?"selected":""}>${t("st_suspended")}</option>
        </select>
      </div>`,
    onSubmit: async close=>{
      const yearVal = parseInt($("#f-year").value, 10);
      const data = {
        plate:$("#f-plate").value.trim(),
        province:$("#f-province").value.trim(),
        owner_name:$("#f-owner").value.trim(),
        unit:$("#f-unit").value.trim(), vehicle_type:$("#f-type").value,
        brand_model:$("#f-brand").value.trim(), color:$("#f-color").value.trim(),
        vehicle_year: Number.isInteger(yearVal) ? yearVal : null,
        valid_until:$("#f-valid").value, status:$("#f-status").value,
      };
      if(!data.plate){ toast(t("need_plate"),"error"); return; }
      if(v) await API.put("/api/vehicles/"+v.id,data);
      else  await API.post("/api/vehicles",data);
      close(); toast(v?t("saved"):t("added"),"success"); reload();
    },
  });
}

/* ---------- view: blacklist ---------- */
async function viewBlacklist(){
  const admin = State.user.role==="admin";
  $("#content").innerHTML = `
    <div class="banner-note">${icon("alert",15)} ${t("bl_note")}</div>
    <div class="toolbar"><div class="spacer"></div>
      ${admin?`<button class="btn btn-primary" id="b-add">${icon("plus",15)} ${t("add_to_bl")}</button>`:""}</div>
    <div class="card"><div class="tbl-wrap"><table>
      <thead><tr><th>${t("th_plate")}</th><th>${t("th_reason")}</th><th>${t("th_added")}</th>${admin?"<th></th>":""}</tr></thead>
      <tbody id="b-body"></tbody></table></div></div>`;
  const load = async ()=>{
    const rows = await API.get("/api/blacklist").catch(()=>[]);
    $("#b-body").innerHTML = rows.map(b=>`<tr>
      <td><span class="t-plate">${esc(b.plate)}</span></td>
      <td>${esc(b.reason||"·")}</td>
      <td class="t-mute">${fmtTime(b.created_at)}</td>
      ${admin?`<td><button class="icon-btn" data-del="${b.id}">${icon("trash",14)}</button></td>`:""}
    </tr>`).join("") || emptyRow(admin?4:3);
    if(admin) $$("[data-del]").forEach(x=>x.onclick=()=>confirmDel("/api/blacklist/"+x.dataset.del,t("q_del_bl"),load));
  };
  if(admin) $("#b-add").onclick = ()=>modal({
    title:t("m_add_bl"),
    body:`<div class="field"><label>${t("f_plate")} *</label><input class="input" id="bl-plate" placeholder="1กข1234"></div>
          <div class="field"><label>${t("f_reason")}</label><input class="input" id="bl-reason"></div>`,
    onSubmit: async close=>{
      const plate=$("#bl-plate").value.trim();
      if(!plate){ toast(t("need_plate"),"error"); return; }
      await API.post("/api/blacklist",{plate,reason:$("#bl-reason").value.trim()});
      close(); toast(t("added"),"success"); load();
    },
  });
  await load();
}

/* ---------- view: reports ---------- */
async function viewReports(){
  const [stats, daily, hourly, top, speed, ocr] = await Promise.all([
    API.get("/api/stats"),
    API.get("/api/reports/daily?days=7"),
    API.get("/api/reports/hourly?days=7"),
    API.get("/api/reports/top-plates?limit=10&days=30"),
    API.get("/api/reports/speed-distribution?days=30"),
    API.get("/api/reports/ocr-distribution?days=30"),
  ]);
  const maxDay = Math.max(1, ...daily.map(d=>d.granted+d.denied+d.alert));
  const maxHr = Math.max(1, ...hourly.map(h=>h.n));
  const maxSp = Math.max(1, ...speed.map(b=>b.n));
  const maxOcr = Math.max(1, ...ocr.map(b=>b.n));
  const today = new Date().toISOString().slice(0,10);
  const monthAgo = new Date(Date.now() - 30*86400e3).toISOString().slice(0,10);
  $("#content").innerHTML = `
    <div class="grid grid-4">
      ${statCard(t("r_total"),stats.total_events,"list","ink")}
      ${statCard(t("r_registered"),stats.registered_vehicles,"car","granted")}
      ${statCard(t("r_blacklisted"),stats.blacklisted,"ban","denied")}
      ${statCard(t("s_today"),stats.today_events,"clock","ink")}
    </div>
    <div class="row section-gap">
      <div class="card" style="flex:1.6">
        <div class="card-head"><div class="card-title">${t("chart_title")}</div></div>
        <div class="card-body">
          <div class="chart">${daily.length?daily.map(d=>chartCol(d,maxDay)).join(""):`<div class="empty" style="width:100%">${t("no_data")}</div>`}</div>
          <div class="legend">
            <span class="legend-item"><span class="legend-dot" style="background:var(--granted)"></span>${t("d_granted")}</span>
            <span class="legend-item"><span class="legend-dot" style="background:var(--denied)"></span>${t("d_denied")}</span>
            <span class="legend-item"><span class="legend-dot" style="background:var(--alert)"></span>${t("d_alert")}</span>
          </div>
        </div>
      </div>
      <div class="card" style="flex:1">
        <div class="card-head"><div class="card-title">${t("breakdown")}</div></div>
        <div class="card-body">
          ${donutBlock([
            {label:t("d_granted"),value:stats.granted,color:"var(--granted)"},
            {label:t("d_denied"),value:stats.denied,color:"var(--denied)"},
            {label:t("d_alert"),value:stats.alert,color:"var(--alert)"},
          ])}
        </div>
      </div>
    </div>

    <div class="card section-gap">
      <div class="card-head">
        <div><div class="card-title">${t("hourly_title")}</div>
          <div class="card-sub">${t("hourly_sub")} · ${peakLabel(hourly)}</div></div>
      </div>
      <div class="card-body">${hourlyChart(hourly)}</div>
    </div>

    <div class="row section-gap">
      <div class="card" style="flex:1">
        <div class="card-head">
          <div><div class="card-title">${t("speed_title")}</div>
            <div class="card-sub">${t("speed_sub")}</div></div>
        </div>
        <div class="card-body"><div class="bar-list">
          ${speed.map(b=>barRow(b.label,b.n,maxSp,b.over_limit?"var(--denied)":"var(--accent)")).join("")}
        </div></div>
      </div>
      <div class="card" style="flex:1">
        <div class="card-head">
          <div><div class="card-title">${t("ocr_title")}</div>
            <div class="card-sub">${t("ocr_sub")}</div></div>
        </div>
        <div class="card-body"><div class="bar-list">
          ${ocr.map((b,i)=>barRow(b.label,b.n,maxOcr,
            i<2?"var(--alert)":(i<3?"var(--accent)":"var(--granted)"))).join("")}
        </div></div>
      </div>
    </div>

    <div class="card section-gap">
      <div class="card-head">
        <div><div class="card-title">${t("top_title")}</div>
          <div class="card-sub">${t("top_sub")}</div></div>
      </div>
      <div class="tbl-wrap"><table>
        <thead><tr>
          <th>${t("th_plate")}</th><th>${t("th_owner")}</th><th>${t("th_type")}</th>
          <th>${t("th_count")}</th><th>${t("d_granted")}</th><th>${t("d_denied")}</th>
          <th>${t("d_alert")}</th><th>${t("th_last_seen")}</th>
        </tr></thead>
        <tbody>${top.length?top.map(topRow).join(""):`<tr><td colspan="8" class="t-mute" style="padding:30px">${t("no_data")}</td></tr>`}</tbody>
      </table></div>
    </div>

    <div class="card section-gap">
      <div class="card-head">
        <div><div class="card-title">${t("export_title")}</div>
          <div class="card-sub">${t("export_sub")}</div></div>
      </div>
      <div class="card-body">
        <div class="export-row">
          <div class="field"><label>${t("export_from")}</label>
            <input class="input" type="date" id="ex-from" value="${monthAgo}"></div>
          <div class="field"><label>${t("export_to")}</label>
            <input class="input" type="date" id="ex-to" value="${today}"></div>
          <div class="field"><label>${t("export_filter")}</label>
            <select class="select" id="ex-dec">
              <option value="">${t("export_all")}</option>
              <option value="granted">${t("d_granted")}</option>
              <option value="denied">${t("d_denied")}</option>
              <option value="alert">${t("d_alert")}</option>
            </select></div>
          <div class="field" style="align-self:flex-end">
            <button class="btn btn-primary" id="ex-btn">${icon("download",15)} ${t("export_btn")}</button>
          </div>
        </div>
      </div>
    </div>`;
  $("#ex-btn").onclick = exportCsv;
}

function peakLabel(hourly){
  const peak = hourly.reduce((a,b)=>b.n>a.n?b:a, {hour:0,n:0});
  if(peak.n === 0) return t("no_data");
  return `${t("peak_at")} ${String(peak.hour).padStart(2,"0")}:00 (${peak.n})`;
}

function hourlyChart(hourly){
  if(!hourly.some(h=>h.n>0)) return `<div class="empty">${t("no_data")}</div>`;
  const W=1200, H=220, padL=42, padR=14, padT=14, padB=30;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const max = Math.max(1, ...hourly.map(h=>h.n));
  const niceMax = niceTop(max);
  const xs = i => padL + (i/23) * innerW;
  const ys = v => padT + innerH - (v/niceMax) * innerH;
  const pts = hourly.map((h,i)=>[xs(i), ys(h.n)]);
  const linePath = "M" + pts.map(p=>p[0].toFixed(1)+","+p[1].toFixed(1)).join(" L");
  const baseY = padT + innerH;
  const areaPath = linePath
    + ` L${xs(23).toFixed(1)},${baseY.toFixed(1)}`
    + ` L${padL.toFixed(1)},${baseY.toFixed(1)} Z`;

  const grid = [0, 0.25, 0.5, 0.75, 1].map(f=>{
    const y = padT + innerH - f*innerH;
    const val = Math.round(f*niceMax);
    return `<line x1="${padL}" y1="${y}" x2="${padL+innerW}" y2="${y}" `
      + `stroke="var(--border)" stroke-dasharray="3 4" />`
      + `<text x="${padL-10}" y="${y+4}" text-anchor="end" `
      + `fill="var(--text-mute)" font-size="13">${val}</text>`;
  }).join("");

  const xLabels = [0,3,6,9,12,15,18,21].map(h=>
    `<text x="${xs(h)}" y="${H-10}" text-anchor="middle" `
    + `fill="var(--text-mute)" font-size="13">${String(h).padStart(2,"0")}:00</text>`
  ).join("");

  const peakIdx = hourly.reduce((bi,h,i,a)=>h.n>a[bi].n?i:bi, 0);
  const pP = pts[peakIdx];
  const peakNum = hourly[peakIdx].n;
  const peakG = `<g class="hr-peak"><line x1="${pP[0]}" y1="${pP[1]}" x2="${pP[0]}" y2="${baseY}" `
    + `stroke="var(--accent)" stroke-dasharray="3 3" stroke-opacity=".5" />`
    + `<circle cx="${pP[0]}" cy="${pP[1]}" r="6" fill="white" stroke="var(--accent)" stroke-width="2.5" />`
    + `<text x="${pP[0]}" y="${pP[1]-14}" text-anchor="middle" font-weight="700" `
    + `font-size="13" fill="var(--accent)">${peakNum}</text></g>`;

  return `<div class="hr-svg-wrap">
    <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" class="hr-svg">
      <defs>
        <linearGradient id="hr-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#2f6bf0" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#2f6bf0" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      ${grid}
      <path d="${areaPath}" fill="url(#hr-grad)" />
      <path d="${linePath}" stroke="#2f6bf0" stroke-width="2.4" fill="none"
            stroke-linejoin="round" stroke-linecap="round" />
      ${peakG}
      ${xLabels}
    </svg></div>`;
}

function niceTop(max){
  // Round up to a nice number for axis. 7 -> 10, 23 -> 25, 47 -> 50, 113 -> 120.
  if(max <= 5) return 5;
  const pow = Math.pow(10, Math.floor(Math.log10(max)));
  const n = max/pow;
  const step = n<=1?1:n<=2?2:n<=2.5?2.5:n<=5?5:10;
  return step*pow;
}

function barRow(label, n, max, color){
  const pct = Math.round(n/max*100);
  return `<div class="bar-item">
    <div class="bar-label">${label}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
    <div class="bar-val">${n}</div></div>`;
}

function topRow(r){
  return `<tr>
    <td><span class="t-plate">${esc(r.plate)}</span></td>
    <td>${esc(r.owner_name||t("unknown"))}</td>
    <td>${vtypeBadge(r.vehicle_type)}</td>
    <td style="font-weight:700">${r.total}</td>
    <td><span style="color:var(--granted);font-weight:600">${r.granted||0}</span></td>
    <td><span style="color:var(--denied);font-weight:600">${r.denied||0}</span></td>
    <td><span style="color:var(--alert);font-weight:600">${r.alert||0}</span></td>
    <td class="t-mute">${fmtTime(r.last_seen)}</td>
  </tr>`;
}

async function exportCsv(){
  const btn = $("#ex-btn");
  const original = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = icon("download",15)+" "+t("exporting");
  try{
    const params = new URLSearchParams();
    const f = $("#ex-from").value, to = $("#ex-to").value, d = $("#ex-dec").value;
    if(f)  params.set("from", f);
    if(to) params.set("to", to);
    if(d)  params.set("decision", d);
    const res = await fetch("/api/reports/export?"+params,
      { headers:{Authorization:"Bearer "+API.token} });
    if(!res.ok) throw new Error("HTTP "+res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `deep_alpr_events_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(url), 1500);
    toast(t("saved"),"success");
  }catch(e){ toast(e.message,"error"); }
  finally{ btn.disabled = false; btn.innerHTML = original; }
}
function chartCol(d,max){
  const h = v=>Math.round(v/max*150);
  const label = new Date(d.day).toLocaleDateString(LANG==="th"?"th-TH":"en-GB",{weekday:"short",day:"numeric"});
  return `<div class="chart-col">
    <div class="chart-bar" title="${d.day}">
      <div class="chart-seg alert" style="height:${h(d.alert)}px"></div>
      <div class="chart-seg denied" style="height:${h(d.denied)}px"></div>
      <div class="chart-seg granted" style="height:${h(d.granted)}px"></div>
    </div><div class="chart-x">${label}</div></div>`;
}
function donutBlock(segs){
  const total = segs.reduce((s,x)=>s+x.value,0) || 1;
  const R = 52, C = 2 * Math.PI * R;
  let off = 0;
  const rings = segs.map(s=>{
    const len = (s.value/total) * C;
    const c = `<circle cx="70" cy="70" r="${R}" fill="none" style="stroke:${s.color}" `
      + `stroke-width="22" stroke-dasharray="${len.toFixed(2)} ${(C-len).toFixed(2)}" `
      + `stroke-dashoffset="${(-off).toFixed(2)}" transform="rotate(-90 70 70)"/>`;
    off += len;
    return c;
  }).join("");
  const legend = segs.map(s=>`<div class="dl-item">
    <span class="dl-dot" style="background:${s.color}"></span><span>${s.label}</span>
    <span class="dl-val">${s.value} · ${Math.round(s.value/total*100)}%</span></div>`).join("");
  return `<div class="donut-wrap">
    <div class="donut">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="${R}" fill="none" style="stroke:var(--surface-2)" stroke-width="22"/>
        ${rings}
      </svg>
      <div class="donut-center"><div class="donut-total">${total}</div><div class="donut-cap">${t("r_total")}</div></div>
    </div>
    <div class="donut-legend">${legend}</div>
  </div>`;
}

/* ---------- view: settings ---------- */
async function viewSettings(){
  const admin = State.user.role === "admin";
  const users = admin ? await API.get("/api/users").catch(()=>[]) : [];
  const me = State.user;
  const reload = ()=>navigate("settings");
  $("#content").innerHTML = `
    <div class="row">
      <div class="card" style="flex:1">
        <div class="card-head"><div class="card-title">${t("set_system")}</div></div>
        <div class="card-body"><div class="kv-list">
          <div class="kv"><span class="k">${t("kv_system")}</span><span class="v">Deep ALPR Access Control v2.0</span></div>
          <div class="kv"><span class="k">${t("kv_gate")}</span><span class="v">${t("gate_main")}</span></div>
          <div class="kv"><span class="k">${t("kv_speed")}</span><span class="v">${t("speed_rule")}</span></div>
          <div class="kv"><span class="k">${t("kv_ocr")}</span><span class="v">CRNN · 99.6%</span></div>
          <div class="kv"><span class="k">${t("retention_label")}</span><span class="v">${t("retention_val")}</span></div>
          <div class="kv"><span class="k">${t("kv_user")}</span><span class="v">${esc(me.display_name)}</span></div>
        </div></div>
      </div>
      <div class="card" style="flex:1">
        <div class="card-head"><div class="card-title">${t("set_integration")}</div></div>
        <div class="card-body">
          <p style="color:var(--text-2);font-size:13px;margin-bottom:14px">${t("integration_desc")}</p>
          <div class="kv-list">
            <div class="kv"><span class="k">${t("kv_rest")}</span><span class="code">/api</span></div>
            <div class="kv"><span class="k">${t("kv_docs")}</span><span class="code">/docs</span></div>
            <div class="kv"><span class="k">${t("kv_webhook")}</span><span class="v">${t("webhook_on")}</span></div>
          </div>
        </div>
      </div>
    </div>
    <div class="card section-gap">
      <div class="card-head"><div class="card-title">${t("account")}</div></div>
      <div class="card-body" style="display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap">
        <div>
          <div style="font-weight:600;font-size:14px">${esc(me.display_name||me.username)}</div>
          <div style="font-size:12px;color:var(--text-mute);margin-top:3px">${esc(me.username)} &nbsp;·&nbsp; ${me.role==="admin"?t("role_admin"):t("role_operator")}</div>
        </div>
        <button class="btn" id="pw-btn">${icon("lock",15)} ${t("change_pw")}</button>
      </div>
    </div>
    ${admin?`<div class="card section-gap">
      <div class="card-head"><div class="card-title">${t("set_users")}</div>
        <button class="btn btn-primary btn-sm" id="u-add">${icon("plus",14)} ${t("add_user")}</button></div>
      <div class="tbl-wrap"><table>
        <thead><tr><th>${t("th_username")}</th><th>${t("th_name")}</th><th>${t("th_role")}</th><th>${t("th_created")}</th><th>${t("th_actions")}</th></tr></thead>
        <tbody>${users.map(u=>rowUser(u, me.id)).join("")}</tbody>
      </table></div></div>`:""}`;
  $("#pw-btn").onclick = changePasswordModal;
  if(admin){
    $("#u-add").onclick = userAddModal;
    $$("[data-edit-u]").forEach(b=>b.onclick=()=>userEditModal(JSON.parse(b.dataset.editU), reload));
    $$("[data-del-u]").forEach(b=>b.onclick=()=>confirmDel("/api/users/"+b.dataset.delU, t("q_del_user"), reload));
  }
}
function rowUser(u, meId){
  const isSelf = u.id === meId;
  return `<tr>
    <td><span class="t-plate" style="font-size:13px">${esc(u.username)}</span></td>
    <td>${esc(u.display_name||"·")}</td>
    <td><span class="badge ${u.role==="admin"?"badge-resident":"badge-staff"}">${u.role==="admin"?t("role_admin"):t("role_operator")}</span></td>
    <td class="t-mute">${fmtTime(u.created_at)}</td>
    <td><div class="t-actions">
      <button class="icon-btn" data-edit-u="${esc(JSON.stringify(u))}">${icon("edit",14)}</button>
      ${isSelf?"":`<button class="icon-btn" data-del-u="${u.id}">${icon("trash",14)}</button>`}
    </div></td></tr>`;
}
function userAddModal(){
  modal({
    title: t("m_add_user"),
    body:`<div class="field"><label>${t("th_username")} *</label><input class="input" id="nu-user"></div>
          <div class="field"><label>${t("f_password")} *</label><input class="input" id="nu-pass" type="password"></div>
          <div class="field"><label>${t("f_name")}</label><input class="input" id="nu-name"></div>
          <div class="field"><label>${t("f_role")}</label><select class="select" id="nu-role">
            <option value="operator">${t("role_operator")}</option><option value="admin">${t("role_admin")}</option></select></div>`,
    onSubmit: async close=>{
      const username=$("#nu-user").value.trim(), password=$("#nu-pass").value;
      if(!username||!password){ toast(t("fill_all"),"error"); return; }
      await API.post("/api/users",{username,password,
        display_name:$("#nu-name").value.trim()||username, role:$("#nu-role").value});
      close(); toast(t("added"),"success"); navigate("settings");
    },
  });
}
function userEditModal(u, reload){
  modal({
    title: t("m_edit_user"),
    body:`<div class="field"><label>${t("th_username")}</label>
            <input class="input" value="${esc(u.username)}" readonly style="opacity:.65;cursor:not-allowed"></div>
          <div class="field"><label>${t("f_name")}</label>
            <input class="input" id="eu-name" value="${esc(u.display_name||"")}"></div>
          <div class="field"><label>${t("f_role")}</label>
            <select class="select" id="eu-role">
              <option value="operator" ${u.role==="operator"?"selected":""}>${t("role_operator")}</option>
              <option value="admin" ${u.role==="admin"?"selected":""}>${t("role_admin")}</option>
            </select></div>
          <div class="field"><label>${t("f_new_pass_optional")}</label>
            <input class="input" id="eu-pass" type="password" placeholder="••••••••"></div>`,
    onSubmit: async close=>{
      await API.put("/api/users/"+u.id, {
        display_name: $("#eu-name").value.trim(),
        role: $("#eu-role").value,
        password: $("#eu-pass").value,
      });
      close(); toast(t("saved"),"success"); reload();
    },
  });
}
function changePasswordModal(){
  modal({
    title: t("m_change_pw"),
    body:`<div class="field"><label>${t("f_current_pass")} *</label><input class="input" id="cp-cur" type="password"></div>
          <div class="field"><label>${t("f_new_pass")} *</label><input class="input" id="cp-new" type="password"></div>
          <div class="field"><label>${t("f_confirm_pass")} *</label><input class="input" id="cp-cnf" type="password"></div>`,
    onSubmit: async close=>{
      const cur=$("#cp-cur").value, nw=$("#cp-new").value, cf=$("#cp-cnf").value;
      if(!cur||!nw||!cf){ toast(t("fill_all"),"error"); return; }
      if(nw !== cf){ toast(t("pw_mismatch"),"error"); return; }
      if(nw.length < 6){ toast(t("pw_short"),"error"); return; }
      await API.post("/api/auth/change-password", {current_password: cur, new_password: nw});
      close(); toast(t("pw_changed"),"success");
    },
  });
}

const VIEWS = {
  console:viewConsole, log:viewLog, vehicles:viewVehicles,
  blacklist:viewBlacklist, reports:viewReports, settings:viewSettings,
};

/* ---------- boot ---------- */
document.addEventListener("click", e=>{
  const img = e.target.closest && e.target.closest("img.zoomable");
  if(!img || !img.dataset.ev) return;
  const id = img.dataset.ev;
  // Demo event (id < 0) lives only in the client -- don't hit the API.
  if(parseInt(id, 10) < 0 && typeof LIVE_DEMO !== "undefined"){
    eventPopup(LIVE_DEMO.event);
    return;
  }
  API.get("/api/events/"+id).then(eventPopup).catch(()=>{});
});
document.documentElement.lang = LANG;
(async function boot(){
  if(API.token){
    try{ State.user = await API.get("/api/auth/me"); renderApp("console"); return; }
    catch(e){ /* fall through */ }
  }
  renderLogin();
})();

})();
