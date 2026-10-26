# Widgetly templates

Templates for the [Widgetly](https://play.google.com/store/apps/details?id=com.widgetly.app)
home screen widget app. The app's gallery downloads `index.json` from here, so
new templates reach everyone without an app update.

- `index.json`: the published templates. Each entry has a gallery `category`
  (shown as a tab) and a `design` in Widgetly's design format.
- Designs an older version of the app can't read are skipped, so adding new
  kinds of templates is safe.

This repo holds only template designs (layouts and colors), no app code.

## Monthly Pro drops

Entries in `index.json` with `"pro": true` and a `released` day ("2026-12-01")
are that month's Pro widgets: hidden until the day, then shown on top of the
template gallery as "<Month> Pro drop", and only Pro can add them.
`scripts/template_drops.py` in the app repo writes them.

## Weekly Pro themes

- `themes.json`: whole-home-screen themes (widget colors, font, stickers, app
  icon colors and a wallpaper), one coming out each week. Each has a
  `released` day ("2026-11-02") and only shows in the app from that day on,
  so weeks can be added ahead of time. The newest ones show under "New this
  week", and the next one is teased with its day.
- `themes/`: their wallpapers (1080×2340 WebP), painted by
  `scripts/weekly_wallpapers.py` in the app repo from Fluent Emoji 3D pictures
  (MIT, github.com/microsoft/fluentui-emoji).
- `stickers` must be names of stickers bundled in the app; unknown ones are
  skipped. `translations` holds the name and tagline in other languages.
- To add a week: paint its wallpaper, add it under `themes/`, then add an
  entry with the next `released` day.

## Web pages

With GitHub Pages turned on (Settings → Pages → Deploy from a branch: `main`,
folder `/`), this repo also serves:

- `look/`: where theme links shared from the app point. It opens the theme in
  Widgetly, or sends people without the app to Google Play.
- `PRIVACY`: the privacy policy, for the Play Store listing.
