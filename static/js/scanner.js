async function validateTicket() {
  const qr_token = document.getElementById("qr_token").value.trim();
  const res = await fetch("/api/validate-ticket", {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({qr_token})});
  const data = await res.json();
  showResult(data);
}

async function checkinTicket() {
  const qr_token = document.getElementById("qr_token").value.trim();
  const gate_name = document.getElementById("gate_name").value.trim();
  const checked_in_by = document.getElementById("checked_in_by").value.trim();
  const res = await fetch("/api/checkin", {method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({qr_token, gate_name, checked_in_by})});
  const data = await res.json();
  showResult(data);
}

function showResult(data) {
  const box = document.getElementById("result");
  box.className = "result";
  if (data.status === "success" || data.status === "valid") box.classList.add("success");
  else if (data.status === "unpaid") box.classList.add("warn");
  else box.classList.add("error");
  box.innerHTML = `<div>${data.message}</div>${data.name ? `<div>الاسم: ${data.name}</div>` : ""}${data.ticket_type ? `<div>النوع: ${data.ticket_type}</div>` : ""}${data.booking_code ? `<div>الكود: ${data.booking_code}</div>` : ""}`;
}
