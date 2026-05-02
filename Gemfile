source "https://rubygems.org"

# Use the GitHub Pages gem so local builds match what GitHub Pages runs.
# This bundles a pinned Jekyll along with the plugin set GitHub Pages allows
# (including jekyll-github-metadata, which powers `site.github.public_repositories`).
gem "github-pages", group: :jekyll_plugins

# Plugins (already included via github-pages, but listed for clarity)
group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-seo-tag"
end

# Windows / JRuby tzinfo
gem "tzinfo-data", platforms: [:mingw, :mswin, :x64_mingw, :jruby]

# Performance booster for watching directories on Windows
gem "wdm", "~> 0.1.0" if Gem.win_platform?
