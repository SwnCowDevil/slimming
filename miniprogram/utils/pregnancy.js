function formatGestation(gestation) {
  if (!gestation || gestation.week == null) return "孕周待完善";
  return `孕 ${gestation.week} 周 ${gestation.day || 0} 天`;
}

function sortSchedules(schedules) {
  return [...(schedules || [])].sort((a, b) => a.position - b.position);
}

function actorLabel(record, currentUserId) {
  return record && record.created_by_user_id === currentUserId ? "我记录" : "家人记录";
}

module.exports = { formatGestation, sortSchedules, actorLabel };
