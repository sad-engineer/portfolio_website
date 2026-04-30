(function () {
  var config = window.__WORK_HOURS_REFRESH__;
  if (!config || typeof config !== "object") {
    return;
  }

  var WEEKDAY_MAP = {
    Mon: 1,
    Tue: 2,
    Wed: 3,
    Thu: 4,
    Fri: 5,
    Sat: 6,
    Sun: 7,
  };

  function parseHHMM(value) {
    if (typeof value !== "string") {
      return null;
    }
    var parts = value.split(":");
    if (parts.length !== 2) {
      return null;
    }
    var hour = Number(parts[0]);
    var minute = Number(parts[1]);
    if (
      Number.isNaN(hour) ||
      Number.isNaN(minute) ||
      hour < 0 ||
      hour > 23 ||
      minute < 0 ||
      minute > 59
    ) {
      return null;
    }
    return hour * 60 + minute;
  }

  function getNowPartsInTimezone(timeZone) {
    try {
      var formatter = new Intl.DateTimeFormat("en-US", {
        timeZone: timeZone || "UTC",
        weekday: "short",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });
      var parts = formatter.formatToParts(new Date());
      var weekday = null;
      var hour = null;
      var minute = null;
      for (var i = 0; i < parts.length; i += 1) {
        if (parts[i].type === "weekday") {
          weekday = WEEKDAY_MAP[parts[i].value] || null;
        } else if (parts[i].type === "hour") {
          hour = Number(parts[i].value);
        } else if (parts[i].type === "minute") {
          minute = Number(parts[i].value);
        }
      }
      if (
        weekday === null ||
        Number.isNaN(hour) ||
        Number.isNaN(minute) ||
        hour < 0 ||
        minute < 0
      ) {
        return null;
      }
      return {
        weekday: weekday,
        minutes: hour * 60 + minute,
      };
    } catch (_error) {
      return null;
    }
  }

  function isWithinWorkingHours() {
    var nowParts = getNowPartsInTimezone(config.timezone);
    if (!nowParts) {
      return Boolean(config.is_within_working_hours);
    }

    var schedule = config.schedule;
    if (schedule && typeof schedule === "object" && !Array.isArray(schedule)) {
      var dayRanges = schedule[String(nowParts.weekday)];
      if (!Array.isArray(dayRanges)) {
        return true;
      }
      for (var i = 0; i < dayRanges.length; i += 1) {
        var range = dayRanges[i];
        if (!range || typeof range !== "object") {
          continue;
        }
        var start = parseHHMM(range.start);
        var end = parseHHMM(range.end);
        if (start === null || end === null) {
          continue;
        }
        if (start <= nowParts.minutes && nowParts.minutes < end) {
          return true;
        }
      }
      return false;
    }

    var workDaysRaw =
      typeof config.work_days === "string" ? config.work_days : "1,2,3,4,5";
    var allowed = {};
    var dayItems = workDaysRaw.split(",");
    for (var d = 0; d < dayItems.length; d += 1) {
      var dayNum = Number(dayItems[d].trim());
      if (!Number.isNaN(dayNum)) {
        allowed[dayNum] = true;
      }
    }
    if (!allowed[nowParts.weekday]) {
      return false;
    }

    var startMinutes = parseHHMM(config.work_hours_start || "09:00");
    var endMinutes = parseHHMM(config.work_hours_end || "18:00");
    if (startMinutes === null || endMinutes === null) {
      return true;
    }
    return startMinutes <= nowParts.minutes && nowParts.minutes < endMinutes;
  }

  var initialState = Boolean(config.is_within_working_hours);
  var isReloading = false;
  var checkIntervalMs = 15000;

  function checkAndReload() {
    if (isReloading) {
      return;
    }
    var currentState = isWithinWorkingHours();
    if (currentState !== initialState) {
      isReloading = true;
      window.location.reload();
    }
  }

  window.setInterval(checkAndReload, checkIntervalMs);
})();
