// ============================================================
// DEMO DATA — داده‌های تستی برای نسخه دمو
// ============================================================
(function() {
  // تاریخ‌های داینامیک (همیشه نسبت به امروز)
  const now = new Date();
  const d = (offsetDays) => {
    const dt = new Date(now);
    dt.setDate(dt.getDate() + offsetDays);
    return dt;
  };
  const iso = (dt) => dt.toISOString().slice(0, 19).replace('T', ' ');

  const yesterday = iso(d(-1));
  const today = iso(d(0));
  const tomorrow = iso(d(1));

  // ----- دوره‌های (دروس) -----
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
  ];

  // ----- تکالیف (Assignments) -----
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
      id: "demo_q_1",
      course_id: "demo_course_1",
      course_name: "کوئرا - برنامه‌نویسی",
      title: "تمرین کوئرا: سری اول",
      description: "",
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

  // ----- رویدادهای دستی (آزمون امروز) -----
  const events = [
    {
      id: "demo_e_1",
      title: "آزمون میان‌ترم",
      event_type: "exam",
      url: null,
      start_at: today.replace('00:00', '10:00'), // ساعت ۱۰ امروز
      end_at: null,
      description: "فصل ۱ تا ۴",
      course_id: "demo_course_1",
      course_name: "مدارهای الکتریکی",
      is_new: false,
    },
  ];

  // ----- پست‌های وال -----
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
  ];

  // ----- محتواها -----
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
  ];

  // ----- اعضای کلاس -----
  const members = [
    { id: "m1", course_id: "demo_course_1", name: "دکتر محمدی", profile_url: "#", member_type: "teacher" },
    { id: "m2", course_id: "demo_course_1", name: "سارا احمدی", profile_url: "#", member_type: "student" },
    { id: "m3", course_id: "demo_course_1", name: "علی رضایی", profile_url: "#", member_type: "student" },
    { id: "m4", course_id: "demo_course_1", name: "مریم کریمی", profile_url: "#", member_type: "student" },
    { id: "m5", course_id: "demo_course_1", name: "حسین موسوی", profile_url: "#", member_type: "student" },
  ];

  // ----- مکان کلاس -----
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
    }
  ];

  // ----- آمار داشبورد -----
  const dashboard = {
    stats: {
      active_courses: 1,
      courses: 1,
      pending_assignments: 1,
      events: 1,
      posts: 1,
      contents: 1,
      assignments: 2,
    },
    upcoming_events: [],
    upcoming_assignments: [assignments[0]],
    recent_posts: [posts[0]],
    recent_changes: [],
    today_events: [events[0]],
  };

  // ----- صادرات -----
  window.DEMO_DATA = {
    courses, assignments, events, posts, contents, members, locations, dashboard,
    courseDetail: {
      course: courses[0],
      contents: contents,
      events: events,
      posts: posts,
      assignments: assignments,
      members: members,
      changes: [],
      locations: locations,
    }
  };
})();