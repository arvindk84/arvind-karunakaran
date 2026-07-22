-- build-date.lua
-- Injects the render date into each document's metadata as `build-date`,
-- so the site footer ("Last updated {{< meta build-date >}}") stays current
-- automatically on every `quarto render`. No external dependencies.
function Meta(meta)
  if meta['build-date'] == nil then
    -- %d is zero-padded (portable across Windows/Linux strftime).
    meta['build-date'] = pandoc.MetaString(os.date('%B %d, %Y'))
  end
  return meta
end
