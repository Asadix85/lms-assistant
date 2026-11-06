// ============================================================
// DEMO DATA — داده‌های تستی برای نسخه دمو (GitHub Pages)
// ============================================================
(function () {
  const now = new Date();
  const d = (offsetDays) => {
    const dt = new Date(now);
    dt.setDate(dt.getDate() + offsetDays);
    return dt;
  };
  const iso = (dt) => dt.toISOString().slice(0, 19).replace("T", " ");

  const yesterday = iso(d(-1));
  const today = iso(d(0));
  const tomorrow = iso(d(1));
  const in3 = iso(d(3));
  const in7 = iso(d(7));

  const courses = [
    {
      id: "demo_course_1",
      name: "مدارهای الکتریکی",
      teacher: "دکتر محمدی",
      code: "۱۲-۳۴۵",
      term: "۰۱",
      domain: "lms4",
      status: "active",
      url: "#/course/demo_course_1",
      group_id: "demo_g1",
      source: "lms",
      is_new: false,
    },
    {
      id: "demo_course_2",
      name: "برنامه‌سازی پیشرفته",
      teacher: "دکتر رضایی",
      code: "۱۲-۳۵۰",
      term: "۰۱",
      domain: "lms4",
      status: "active",
      url: "#/course/demo_course_2",
      group_id: "demo_g2",
      source: "lms",
      is_new: true,
    },
  ];

  const assignments = [
    {
      id: "demo_a_1",
      course_id: "demo_course_1",
      course_name: "مدارهای الکتریکی",
      title: "تمرین شماره ۱: تحلیل مدار",
      description: "حل مسائل فصل ۲ کتاب مدارهای الکتریکی",
      deadline: yesterday,
      deadline_jalali: "دیروز",
      submit_url: null,
      view_url: null,
      is_new: false,
      is_manual: false,
      is_done: false,
      is_expired: true,
      source: "lms",
    },
    {
      id: "demo_a_2",
      course_id: "demo_course_2",
      course_name: "برنامه‌سازی پیشرفته",
      title: "پروژه میان‌ترم: سیستم مدیریت کتابخانه",
      description: "پیاده‌سازی با Java و ساختار داده مناسب",
      deadline: in3,
      deadline_jalali: "۳ روز دیگر",
      submit_url: null,
      view_url: null,
      is_new: true,
      is_manual: false,
      is_done: false,
      is_expired: false,
      source: "lms",
    },
    {
      id: "demo_q_1",
      course_id: "demo_quera_1",
      course_name: "کوئرا - برنامه‌نویسی",
      title: "تمرین کوئرا: سری اول",
      description: "حل مسائل الگوریتمی",
      deadline: tomorrow,
      deadline_jalali: "فردا",
      submit_url: null,
      view_url: null,
      is_new: false,
      is_manual: false,
      is_done: false,
      is_expired: false,
      source: "quera",
    },
  ];

  const events = [
    {
      id: "demo_e_1",
      title: "آزمون میان‌ترم",
      event_type: "exam",
      url: null,
      start_at: today.replace("00:00", "10:00"),
      end_at: null,
      description: "فصل ۱ تا ۴",
      course_id: "demo_course_1",
      course_name: "مدارهای الکتریکی",
      is_new: false,
    },
    {
      id: "demo_e_2",
      title: "جلسه آنلاین رفع اشکال",
      event_type: "live_session",
      url: null,
      start_at: in7.replace("00:00", "16:00"),
      end_at: null,
      description: "از طریق Adobe Connect",
      course_id: "demo_course_2",
      course_name: "برنامه‌سازی پیشرفته",
      is_new: true,
    },
  ];

  const posts = [
    {
      id: "demo_p_1",
      course_id: "demo_course_1",
      author: "دکتر محمدی",
      author_id: "teacher_1",
      text: "سلام به همه. لطفاً فایل جزوه فصل ۳ را حتماً مطالعه کنید.",
      posted_at: yesterday,
      posted_at_jalali: "دیروز",
      post_url: null,
      is_new: true,
    },
    {
      id: "demo_p_2",
      course_id: "demo_course_2",
      author: "دکتر رضایی",
      author_id: "teacher_2",
      text: "مهلت ارسال پروژه تا پایان هفته تمدید شد.",
      posted_at: today,
      posted_at_jalali: "امروز",
      post_url: null,
      is_new: true,
    },
  ];

  const contents = [
    {
      id: "demo_c_1",
      course_id: "demo_course_1",
      course_name: "مدارهای الکتریکی",
      teacher: "دکتر محمدی",
      title: "جزوه فصل ۳",
      url: "#",
      content_type: "pdf",
      filename: "chapter3.pdf",
      last_seen_at: yesterday,
    },
    {
      id: "demo_c_2",
      course_id: "demo_course_2",
      course_name: "برنامه‌سازی پیشرفته",
      teacher: "دکتر رضایی",
      title: "اسلایدهای جلسه ۵",
      url: "#",
      content_type: "pdf",
      filename: "session5.pdf",
      last_seen_at: today,
    },
  ];

  const members = [
    { id: "m1", course_id: "demo_course_1", name: "دکتر محمدی", profile_url: "#", member_type: "teacher" },
    { id: "m2", course_id: "demo_course_1", name: "سارا احمدی", profile_url: "#", member_type: "student" },
    { id: "m3", course_id: "demo_course_1", name: "علی رضایی", profile_url: "#", member_type: "student" },
    { id: "m4", course_id: "demo_course_1", name: "مریم کریمی", profile_url: "#", member_type: "student" },
    { id: "m5", course_id: "demo_course_1", name: "حسین موسوی", profile_url: "#", member_type: "student" },
  ];

  const locations = [
    {
      weekday: "امروز",
      start_time: "10:00",
      end_time: "12:00",
      location_text: "ساختمان فنی قدیم - کلاس ۱۰۱",
      faculty: "دانشکده فنی و مهندسی",
      building: "مجتمع کلاس‌ها",
      lat: 32.601704,
      lng: 51.658592,
      course_name: "مدارهای الکتریکی",
    },
    {
      weekday: "یکشنبه",
      start_time: "14:00",
      end_time: "16:00",
      location_text: "ساختمان مهندسی - کلاس ۲۰۵",
      faculty: "دانشکده فنی و مهندسی",
      building: "ساختمان مهندسی",
      lat: 32.6021,
      lng: 51.6592,
      course_name: "برنامه‌سازی پیشرفته",
    },
  ];

  const queraCourses = [
    {
      id: "demo_quera_1",
      name: "برنامه‌نویسی پیشرفته",
      url: "#",
      source: "quera",
    },
  ];

  const queraAssignments = [
    {
      id: "demo_q_1",
      course_id: "demo_quera_1",
      course_name: "برنامه‌نویسی پیشرفته",
      title: "تمرین کوئرا: سری اول",
      deadline: tomorrow,
      deadline_jalali: "فردا",
      is_done: false,
      is_expired: false,
      source: "quera",
    },
  ];

  const changes = [
    {
      id: "ch1",
      course_id: "demo_course_1",
      course_name: "مدارهای الکتریکی",
      change_type: "content",
      title: "جزوه فصل ۳ اضافه شد",
      changed_at: yesterday,
      changed_at_jalali: "دیروز",
    },
    {
      id: "ch2",
      course_id: "demo_course_2",
      course_name: "برنامه‌سازی پیشرفته",
      change_type: "assignment",
      title: "پروژه میان‌ترم منتشر شد",
      changed_at: today,
      changed_at_jalali: "امروز",
    },
  ];

  const dashboard = {
    stats: {
      active_courses: courses.length,
      courses: courses.length,
      pending_assignments: assignments.filter((a) => !a.is_done && !a.is_expired).length,
      events: events.length,
      posts: posts.length,
      contents: contents.length,
      assignments: assignments.length,
    },
    upcoming_events: events.filter((e) => e.start_at >= today),
    upcoming_assignments: assignments.filter((a) => !a.is_expired && !a.is_done),
    recent_posts: posts,
    recent_changes: changes,
    today_events: events.filter((e) => e.start_at.startsWith(today.slice(0, 10))),
  };

  window.DEMO_DATA = {
    courses,
    assignments,
    events,
    posts,
    contents,
    members,
    locations,
    changes,
    queraCourses,
    queraAssignments,
    dashboard,
    courseDetail: {
      course: courses[0],
      contents,
      events,
      posts,
      assignments: assignments.filter((a) => a.course_id === "demo_course_1"),
      members,
      changes,
      locations,
    },
  };
})();
