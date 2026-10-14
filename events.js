/* halimozturk.com — family events component v1.0 (2026-10-14). Copy verbatim; edit here.
   Fills <div class="wrap evt" id="now-in-app" hidden></div> from /events/events.json in the page's
   language (the event's own App Store text per locale; en-US when a locale has none). Shows nothing
   when there is no live event and no past one, so a site can carry it before its first event.
   Re-renders when the page switches language in place (Lomel's i18n.js sets <html lang>). */
(function () {
  var el = document.getElementById('now-in-app');
  if (!el || !window.fetch) return;
  var L = {
    en: ['Now in the app', 'Until {d}', 'Starts {d}', 'See the event', 'Past events'],
    tr: ['Şimdi uygulamada', '{d} tarihine kadar', '{d} tarihinde başlıyor', 'Etkinliğe git', 'Geçmiş etkinlikler'],
    de: ['Jetzt in der App', 'Bis {d}', 'Ab {d}', 'Zum Event', 'Vergangene Events'],
    fr: ["En ce moment dans l'app", "Jusqu'au {d}", 'À partir du {d}', "Voir l'événement", 'Événements passés'],
    es: ['Ahora en la app', 'Hasta el {d}', 'Desde el {d}', 'Ver el evento', 'Eventos anteriores'],
    it: ["Ora nell'app", 'Fino al {d}', 'Dal {d}', "Vedi l'evento", 'Eventi passati'],
    pt: ['Agora no app', 'Até {d}', 'A partir de {d}', 'Ver o evento', 'Eventos anteriores'],
    nl: ['Nu in de app', 'Tot {d}', 'Vanaf {d}', 'Bekijk het evenement', 'Eerdere evenementen'],
    sv: ['Nu i appen', 'Till {d}', 'Från {d}', 'Se evenemanget', 'Tidigare evenemang'],
    da: ['Nu i appen', 'Til {d}', 'Fra {d}', 'Se begivenheden', 'Tidligere begivenheder'],
    no: ['Nå i appen', 'Til {d}', 'Fra {d}', 'Se arrangementet', 'Tidligere arrangementer'],
    pl: ['Teraz w aplikacji', 'Do {d}', 'Od {d}', 'Zobacz wydarzenie', 'Poprzednie wydarzenia'],
    ru: ['Сейчас в приложении', 'До {d}', 'С {d}', 'Смотреть событие', 'Прошедшие события'],
    ja: ['アプリで開催中', '{d}まで', '{d}から', 'イベントを見る', '過去のイベント'],
    ko: ['지금 앱에서', '{d}까지', '{d}부터', '이벤트 보기', '지난 이벤트'],
    'zh-hans': ['应用内活动进行中', '截至{d}', '{d}开始', '查看活动', '往期活动'],
    'zh-hant': ['App 內活動進行中', '至{d}', '{d}開始', '查看活動', '往期活動']
  };
  var lang, t, data;
  function setLang() {
    lang = (document.documentElement.lang || 'en').toLowerCase();
    if (lang === 'nb' || lang === 'nn') lang = 'no';
    t = L[lang] || L[lang.split('-')[0]] || L.en;
  }
  function text(ev) {
    var tx = ev.text || {}, ks = Object.keys(tx), want = lang === 'en' ? 'en-us' : lang;
    for (var i = 0; i < ks.length; i++) if (ks[i].toLowerCase() === want) return tx[ks[i]];
    for (i = 0; i < ks.length; i++) if (ks[i].toLowerCase().split('-')[0] === want.split('-')[0]) return tx[ks[i]];
    return tx['en-US'] || tx[ks[0]] || { name: '', short: '' };
  }
  function esc(s) { return String(s || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function day(iso) {
    try { return new Intl.DateTimeFormat(document.documentElement.lang || 'en', { month: 'long', day: 'numeric' }).format(new Date(iso)); }
    catch (e) { return iso.slice(0, 10); }
  }
  function render(d) {
    setLang();
    var now = Date.now(), html = '';
    var live = (d.now || []).filter(function (e) { return Date.parse(e.publish) <= now && Date.parse(e.end) > now; })[0];
    if (live) {
      var x = text(live), started = Date.parse(live.start) <= now;
      var when = (started ? t[1] : t[2]).replace('{d}', day(started ? live.end : live.start));
      html += '<a class="evt-now" href="' + esc(live.url) + '" target="_blank" rel="noopener">' +
        '<img src="/' + esc(live.card) + '" width="1280" height="720" alt="" loading="lazy">' +
        '<div class="evt-body"><p class="evt-eyebrow">' + esc(t[0]) + '</p><h3>' + esc(x.name) + '</h3><p>' + esc(x.short) + '</p>' +
        '<div class="evt-meta"><span class="evt-cta">' + esc(t[3]) +
        ' <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 11 11 5M6 5h5v5"/></svg></span>' +
        '<span class="evt-when">' + esc(when) + '</span></div></div></a>';
    }
    var past = (d.past || []).filter(function (e) { return e.thumb; });
    if (past.length) {
      html += '<div class="evt-past"><h4>' + esc(t[4]) + '</h4><ul class="evt-strip">' + past.map(function (e) {
        var x = text(e);
        return '<li><img src="/' + esc(e.thumb) + '" width="640" height="360" alt="' + esc(x.name) + '" loading="lazy"><span>' + esc(x.name) + '</span></li>';
      }).join('') + '</ul></div>';
    }
    if (html) { el.innerHTML = html; el.hidden = false; }
  }
  fetch('/events/events.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d) return;
    data = d; render(d);
    if (window.MutationObserver) new MutationObserver(function () { render(data); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  }).catch(function () {});
})();
