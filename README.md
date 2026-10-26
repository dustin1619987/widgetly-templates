# Widgetly templates

Templates for the [Widgetly](https://play.google.com/store/apps/details?id=com.widgetly.app)
home screen widget app. The app's gallery downloads `index.json` from here, so
new templates reach everyone without an app update.

- `index.json`: the published templates. Each entry has a gallery `category`
  (shown as a tab) and a `design` in Widgetly's design format.
- Designs an older version of the app can't read are skipped, so adding new
  kinds of templates is safe.

This repo holds only template designs (layouts and colors), no app code.

## Web pages

With GitHub Pages turned on (Settings → Pages → Deploy from a branch: `main`,
folder `/`), this repo also serves:

- `look/`: where theme links shared from the app point. It opens the theme in
  Widgetly, or sends people without the app to Google Play.
- `PRIVACY`: the privacy policy, for the Play Store listing.
