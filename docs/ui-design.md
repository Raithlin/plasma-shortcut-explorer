# KDE interface design

The October 2026 interface revision follows the current [KDE Human Interface
Guidelines](https://develop.kde.org/hig/). The app retains Qt Widgets; KDE
[recommends Kirigami for new apps, while applying the general principles to both
toolkits](https://develop.kde.org/hig/kde_app_design/).

## Decisions

- Use a standard decorated window, with the title in the system titlebar. It
  remains open when focus moves to another application. Escape still closes it.
- Put search and related actions above the content and the count below it, using
  the [layout and navigation guidance](https://develop.kde.org/hig/layout_and_nav/).
  Use Qt's style metrics for margins and spacing, and the system font throughout.
- Give action, application, and assigned shortcut separate columns with native
  item rendering and alternating row colors. Category headings remain a single
  level of non-collapsible sections. Remove custom keycap widgets, fixed row
  heights, and the wide outer gutter, following the [content
  guidance](https://develop.kde.org/hig/displaying_content/).
- Read action icons from the active [icon theme](https://develop.kde.org/hig/icons/).
  Keep text labels on buttons. Do not override the application style or palette.
- Keep labels short, add button mnemonics, and omit an ellipsis from the search
  placeholder, following the [text and label guidance](https://develop.kde.org/hig/text_and_labels/).
- Use native settings groups within a scroll area. This keeps controls accessible
  in smaller windows and at larger system font sizes, as called for in the
  [accessibility guidance](https://develop.kde.org/hig/accessibility/).

`/` and Ctrl+F focus search and select the existing query. A slash typed while
search already has focus remains ordinary text. Ctrl+, opens settings; Ctrl+R
refreshes the discovered bindings. No global shortcuts are registered by these
window-local actions.

## Validation

The full suite covers navigation, search shortcuts, literal slash entry, focus
loss, resizing, settings scrolling at 14-point system text, and inherited light
and dark window colors. Discovery integration tests use the isolated private bus.

The updated screenshots were captured from the source app running in the live
Plasma Wayland session with the installed Breeze widget style and the user's
current theme, font, and icons. Discovery returned 123 assigned shortcuts without
errors. The search screenshot uses the query `window`. The captures use Qt's
window grab and show client content; compositor titlebars and borders are outside
these images. Launching on Wayland does not by itself verify interactive edge
resizing, task switching, or placement across monitors; those remain manual checks.

No shortcut settings, system appearance settings, or window rules are changed by
this interface revision.
