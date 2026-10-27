param([string]$SkinDirectory = (Join-Path $PSScriptRoot '..'))

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

function Assert-True([bool]$Condition, [string]$Message) {
  if (!$Condition) { throw $Message }
}

# Literal textures are packed into media/Textures.xbt; only the process-info channel
# diagrams are kept loose. Resolve against both locations instead of the loose folder alone.
$textureBundle = [System.Text.Encoding]::GetEncoding(28591).GetString(
  [System.IO.File]::ReadAllBytes((Join-Path $SkinDirectory 'media/Textures.xbt')))
function Test-SkinTexture([string]$RelativePath) {
  if (Test-Path -LiteralPath (Join-Path $SkinDirectory ('media/' + $RelativePath))) { return $true }
  return $textureBundle.IndexOf($RelativePath + [char]0, [System.StringComparison]::Ordinal) -ge 0
}

$documents = @{}
$includes = @{}
$variables = @{}
foreach ($file in Get-ChildItem (Join-Path $SkinDirectory 'xml') -Filter '*.xml') {
  $document = [xml](Get-Content -Raw -LiteralPath $file.FullName)
  $documents[$file.Name] = $document
  foreach ($node in $document.SelectNodes('/includes/include[@name]')) { $includes[$node.GetAttribute('name')] = $node }
  foreach ($node in $document.SelectNodes('/includes/variable[@name]')) { $variables[$node.GetAttribute('name')] = $true }
}

foreach ($name in @('MusicVisualisation.xml', 'MusicOSD.xml', 'Includes_MusicPlayer.xml', 'Includes_MusicBackground.xml',
                    'Custom_1114_MusicPlaylistDialog.xml', 'Custom_1113_MusicAudioDialog.xml', 'script-cu-lrclyrics-main.xml')) {
  $document = $documents[$name]
  Assert-True ($null -ne $document) "Missing XML: $name"
  foreach ($node in $document.SelectNodes('//include[not(@name) and not(@file)]')) {
    $reference = if ($node.HasAttribute('content')) { $node.GetAttribute('content') } else { $node.InnerText }
    Assert-True ($includes.ContainsKey($reference)) "Unresolved include: $name $reference"
  }
  foreach ($match in [regex]::Matches($document.OuterXml, '\$VAR\[([^,\]]+)')) {
    Assert-True ($variables.ContainsKey($match.Groups[1].Value)) "Unresolved variable: $name $match"
  }
  foreach ($node in $document.SelectNodes('//*[starts-with(local-name(),"texture") or local-name()="midtexture" or local-name()="righttexture"]')) {
    if ($node.InnerText -and !$node.InnerText.StartsWith('$')) {
      Assert-True (Test-SkinTexture $node.InnerText) "Missing texture: $name $($node.InnerText)"
    }
  }
  foreach ($glass in $document.SelectNodes('//*[@material="glass"]')) {
    Assert-True ($glass.glassstyle -eq 'regular') "Unknown glass preset: $name"
    foreach ($attribute in $glass.Attributes) {
      Assert-True ($attribute.Name -in @('material', 'glassstyle', 'cornerradius')) "Music must use unchanged glass presets: $name $attribute"
    }
  }
}

function Expand-Includes($node) {
  while ($node.SelectSingleNode('./include')) {
    foreach ($inc in @($node.SelectNodes('./include'))) {
      $name = if ($inc.HasAttribute('content')) { $inc.GetAttribute('content') } else { $inc.InnerText }
      $definition = $includes[$name]
      Assert-True ($null -ne $definition) "Unknown include: $name"
      $parameters = @{}
      foreach ($param in $definition.SelectNodes('./param')) { $parameters[$param.GetAttribute('name')] = $param.InnerText }
      foreach ($param in $inc.SelectNodes('./param')) {
        $parameters[$param.GetAttribute('name')] = if ($param.HasAttribute('value')) { $param.GetAttribute('value') } else { $param.InnerText }
      }
      $body = $definition.SelectSingleNode('./definition')
      if (!$body) { $body = $definition }
      foreach ($child in @($body.ChildNodes)) {
        if ($child.NodeType -ne 'Element' -or $child.Name -eq 'param') { continue }
        $raw = $child.OuterXml
        foreach ($param in $parameters.Keys) { $raw = $raw.Replace('$PARAM[' + $param + ']', [System.Security.SecurityElement]::Escape($parameters[$param])) }
        $fragment = $node.OwnerDocument.CreateDocumentFragment()
        $fragment.InnerXml = $raw
        [void]$node.InsertBefore($fragment, $inc)
      }
      [void]$node.RemoveChild($inc)
    }
  }
  foreach ($child in @($node.SelectNodes('./*'))) { Expand-Includes $child }
}

$page = $documents['MusicVisualisation.xml']
$controls = $documents['Includes_MusicPlayer.xml']
Assert-True ($null -ne $documents['Includes.xml'].SelectSingleNode('//include[@file="Includes_MusicBackground.xml"]')) 'Background definitions must be loaded'
Assert-True ($page.SelectSingleNode('/window/controls/include').InnerText -eq 'NaraMusicPlayerBackground') 'Player background include changed'
Assert-True ($page.window.defaultcontrol.InnerText -eq '602') 'Default focus must remain play/pause'
$timedLyrics = $page.SelectSingleNode('//control[@id="420"]')
$plainLyrics = $page.SelectSingleNode('//control[@id="421"]')
Assert-True ($timedLyrics.left -eq $plainLyrics.left -and $timedLyrics.top -eq $plainLyrics.top -and $timedLyrics.height -eq $plainLyrics.height) 'Timed and untimed lyrics must share a column'
Assert-True ([int]$timedLyrics.left + [int]$timedLyrics.width -eq 1760) 'Lyrics must retain the right margin'
Assert-True ($page.OuterXml -notmatch 'LOCALIZE\[24013\]') 'Redundant lyrics heading returned'
$heading = $page.SelectNodes('//control[@type="label" and contains(label,"LOCALIZE[31000]")]')
Assert-True ($heading.Count -eq 1 -and $heading[0].left -eq '40' -and $heading[0].top -eq '28') 'Only the inset top-left now-playing heading is allowed'
$trackPosition = $page.SelectSingleNode('//control[contains(label,"Playlist.Position(music)")]')
Assert-True ($null -ne $trackPosition -and $trackPosition.top -eq '64') 'Missing music track position'
$clock = $page.SelectSingleNode('//control[label="$INFO[System.Time]"]')
$homeClock = $documents['Home.xml'].SelectSingleNode('//control[label="$INFO[System.Time]"]')
Assert-True ($homeClock.visible -eq '!Window.IsVisible(notification) + !Window.IsVisible(extendedprogressdialog)') 'Home clock must yield to notifications and background progress'
Assert-True ($clock.font -eq $homeClock.font -and $clock.right -eq $homeClock.right -and $clock.width -eq $homeClock.width) 'Music clock must match Home font and horizontal position'
Assert-True ([int]$clock.top + [int]$clock.height / 2 -eq ([int]$heading[0].top + [int]$trackPosition.top + [int]$trackPosition.height) / 2) 'Clock must center against both header lines'
foreach ($label in @($heading[0], $trackPosition, $clock)) {
  $font = $documents['Font.xml'].SelectSingleNode('//font[name="' + $label.font + '"]')
  Assert-True ($null -ne $font -and !$font.aspect -and $label.font -notmatch 'narrow') 'Header text must not use condensed fonts or horizontal scaling'
}
$cover = $page.SelectSingleNode('//control[texture="$VAR[NaraMusicCoverVar]"]')
$title = $page.SelectSingleNode('//control[label="$INFO[Player.Title]"]')
Assert-True ($cover.width -eq '450' -and $cover.height -eq '450') 'Music cover must remain 450 pixels square'
Assert-True ($cover.left -eq $title.left) 'Cover must align with its title'
# The lyric column is deliberately raised above the cover top; it only has to clear the header
# above and the bottom control bar (1080 - 160) below.
Assert-True ([int]$timedLyrics.top -lt [int]$cover.top) 'The raised lyric column must start above the cover top'
Assert-True ([int]$timedLyrics.top -ge 96 -and [int]$timedLyrics.top + [int]$timedLyrics.height -le 920) 'Lyric column must clear the header and the bottom control bar'
Assert-True ([int]$title.left + [int]$title.width -lt [int]$timedLyrics.left) 'Song title must not overlap lyrics'
$album = $page.SelectSingleNode('//control[label="$VAR[NaraMusicAlbumYearVar]"]')
Assert-True ([int]$album.top -ge [int]$cover.top + [int]$cover.height) 'Album metadata must sit below the cover'
$details = $page.SelectSingleNode('//control[include/@content="NaraMusicAudioDetail"]')
Assert-True ($details.align -eq 'right' -and [int]$details.right -eq 1920 - [int]$timedLyrics.left - [int]$timedLyrics.width) 'Audio specifications must align with the lyric column right edge'
Assert-True ($details.SelectNodes('include[@content="NaraMusicAudioDetail"]').Count -eq 5) 'Audio specifications must include codec, bit depth, sample rate, bitrate and channels'
$glow = $page.SelectSingleNode('//control[@id="431"]/texture')
Assert-True (!$glow.HasAttribute('border') -and !$glow.HasAttribute('cornerradius')) 'Cover backlight must use a continuous gradient'
Assert-True ($page.SelectSingleNode('//control[@id="432"]').type -eq 'grouplist') 'Cover reflection requires a clipping container'
Assert-True ($page.SelectNodes('//visible[contains(text(),"1114")]').Count -eq 0) 'Lyrics must stay visible behind the playlist popup'
Assert-True ($page.SelectNodes('//*[@material="glass"]').Count -eq 0) 'The clock must be plain text without a glass capsule'
Assert-True ($page.OuterXml -notmatch 'Player.ShowInfo|Player.ShowTime|ColoredBackgroundImages|osdfade') 'Music content must stay persistent and unmasked'
$gate = $page.SelectSingleNode('//include[text()="NaraMusicPlayerControls"]/../visible')
Assert-True ($gate.InnerText -eq '!Window.IsVisible(musicosd)') 'Main controls must not overlap MusicOSD controls'

$lyricsAddon = $documents['script-cu-lrclyrics-main.xml']
$addonList = $lyricsAddon.SelectSingleNode('//control[@id="110"]')
Assert-True ($addonList.type -eq 'list' -and $lyricsAddon.SelectSingleNode('//control[@id="200"]').type -eq 'label') 'CU LRC requires list 110 and source label 200'
Assert-True ($lyricsAddon.SelectNodes('//include | //texture | //texturebackground | //backgroundcolor').Count -eq 0) 'The lyrics overlay must not obscure the music page with a panel or scrim'
$adapterSlide = $addonList.SelectSingleNode('animation[@effect="slide"]')
Assert-True ($adapterSlide.end -eq '0,-10000' -and $adapterSlide.condition.Contains('NaraMusic.IntegratedLyrics')) 'Only the integrated add-on adapter must stay offscreen'
# The add-on window is fused onto the native lyric column: identical geometry, row heights and
# fonts, so the two renderers hand the column over without a visible jump.
Assert-True ($addonList.left -eq $timedLyrics.left -and $addonList.top -eq $timedLyrics.top -and
             $addonList.width -eq $timedLyrics.width -and $addonList.height -eq $timedLyrics.height) 'Add-on lyrics must match the native lyric column geometry'
$addonItem = $addonList.SelectSingleNode('itemlayout')
$addonFocus = $addonList.SelectSingleNode('focusedlayout')
Assert-True ($addonItem.height -eq $timedLyrics.SelectSingleNode('itemlayout').height -and
             $addonFocus.height -eq $timedLyrics.SelectSingleNode('focusedlayout').height) 'Add-on lyric rows must match the native row heights'
Assert-True ($addonItem.SelectSingleNode('control/font').InnerText -eq $timedLyrics.SelectSingleNode('itemlayout/control/font').InnerText) 'Add-on context lyrics must reuse the native font'
Assert-True ($addonFocus.SelectSingleNode('control/font').InnerText -eq $timedLyrics.SelectSingleNode('focusedlayout/control/font').InnerText) 'Add-on focused lyric must reuse the native font'
Assert-True ($null -ne $addonList.SelectSingleNode('animation[@type="WindowOpen"]') -and $addonList.SelectSingleNode('scrolltime').InnerText -eq '200') 'Add-on lyrics must slide in and scroll like the native column'
Assert-True ($lyricsAddon.SelectNodes('//onleft | //onright | //onclick | //onload').Count -eq 0) 'The add-on adapter must not introduce a second navigation mode'
# Native lyrics yield the column while the add-on window owns it, and come back when it closes.
foreach ($lyricControl in @($timedLyrics, $plainLyrics, $page.SelectSingleNode('//control[@id="422"]'))) {
  Assert-True ($lyricControl.SelectSingleNode('visible').InnerText -match '!Window\.IsVisible\(script-cu-lrclyrics-main\.xml\)') "Native lyrics must yield to the add-on window: $($lyricControl.id)"
}
$emptyLyrics = $page.SelectSingleNode('//visible[contains(text(),"NaraMusic.LyricsTimed") and contains(text(),"NaraMusic.LyricsText")]')
Assert-True ($null -ne $emptyLyrics -and $emptyLyrics.InnerText -match '!Window\.IsVisible\(script-cu-lrclyrics-main\.xml\)') 'The empty lyric placeholder must also yield to the add-on window'

$expanded = [xml]$page.OuterXml
Expand-Includes $expanded.window
Assert-True (!$expanded.OuterXml.Contains('$PARAM[')) 'Unresolved player include parameter'
$ids = @($expanded.SelectNodes('//control[@id]'))
Assert-True (@($ids | Group-Object { $_.GetAttribute('id') } | Where-Object Count -gt 1).Count -eq 0) 'Duplicate expanded control IDs'
$buttons = $expanded.SelectNodes('//control[@id="200"]/control/control[@type="radiobutton"]')
$buttonIds = @($buttons | ForEach-Object { $_.GetAttribute('id') })
$order = $buttonIds -join ','
Assert-True ($order -eq '70054,70053,70051,602,600,607,70048') 'Player button order changed'
Assert-True ($buttons[3].onclick -eq 'PlayerControl(Play)') 'Centered button must play/pause'
$checkedIcons = @{}
foreach ($button in $buttons) {
  Assert-True ($button.width -eq '61' -and $button.height -eq '61') 'Buttons must be about 15 percent smaller'
  Assert-True ([int]$button.radiowidth + 2 * [int]$button.radioposx -eq [int]$button.width) 'Icon must center in its button'
  Assert-True ($button.onup -eq '87') 'Every nested button must navigate up to the seek bar'
  Assert-True ($button.texturefocus.colordiffuse -eq 'glass_focus_medium') 'Focus must reuse the shared glass highlight'
  Assert-True ($button.SelectSingleNode('./textureradioonfocus').colordiffuse -eq 'text_primary') 'Focused icons must stay white'
  Assert-True ($button.ParentNode.SelectSingleNode('./control[@type="image"]/texture').glassstyle -eq 'regular') 'Every button needs an independent regular glass background'
  Assert-True ($button.SelectNodes('./*[starts-with(local-name(),"textureradio") and contains(text(),"$VAR[")]').Count -eq 0) 'Radio textures do not support dynamic filenames'
  foreach ($state in @('onfocus', 'onnofocus', 'ondisabled', 'offfocus', 'offnofocus', 'offdisabled')) {
    # The factory uses the first matching texture, including overrides before an include.
    $texture = $button.SelectSingleNode('./textureradio' + $state)
    $path = $texture.InnerText
    Assert-True (![string]::IsNullOrEmpty($path) -and !$path.Contains('$')) "Missing static icon: $($button.id) $state"
    if ($checkedIcons.ContainsKey($path)) { continue }
    $iconPath = Join-Path $SkinDirectory ('media/' + $path)
    # Only loose icons can be decoded here; packed ones are verified through the bundle instead.
    if (Test-Path -LiteralPath $iconPath) {
      $icon = [System.Drawing.Bitmap]::new($iconPath)
      try {
        $visiblePixels = 0
        for ($y = 0; $y -lt $icon.Height; $y++) {
          for ($x = 0; $x -lt $icon.Width; $x++) {
            if ($icon.GetPixel($x, $y).A -gt 0) { $visiblePixels++ }
          }
        }
        Assert-True ($visiblePixels -gt 0) "Icon is fully transparent: $path"
      }
      finally { $icon.Dispose() }
    }
    else {
      Assert-True (Test-SkinTexture $path) "Icon is missing from the texture bundle: $path"
    }
    $checkedIcons[$path] = $true
  }
}
Assert-True ($null -eq $expanded.SelectSingleNode('//control[@id="200"]/texturebackground')) 'OSD buttons must not share a long glass capsule'
$buttonRow = $expanded.SelectSingleNode('//control[@id="200"]')
Assert-True ($buttonRow.itemgap -eq '16') 'Independent buttons need spacing'
Assert-True ([int]$buttonRow.ParentNode.height - [int]$buttonRow.top - [int]$buttonRow.height -eq 20) 'Buttons need 20 pixels of bottom padding'
for ($i = 0; $i -lt $buttons.Count; $i++) {
  Assert-True ($buttons[$i].onleft -eq $buttons[($i + $buttons.Count - 1) % $buttons.Count].id) "Missing direct left navigation: $($buttons[$i].id)"
  Assert-True ($buttons[$i].onright -eq $buttons[($i + 1) % $buttons.Count].id) "Missing direct right navigation: $($buttons[$i].id)"
}
for ($disabled = 0; $disabled -lt (1 -shl $buttons.Count) - 1; $disabled++) {
  for ($i = 0; $i -lt $buttons.Count; $i++) {
    if ($disabled -band (1 -shl $i)) { continue }
    foreach ($direction in @('onleft', 'onright')) {
      $next = $i
      for ($step = 0; $step -lt $buttons.Count; $step++) {
        $target = $buttons[$next].SelectSingleNode('./' + $direction).InnerText
        $next = [array]::IndexOf($buttonIds, $target)
        Assert-True ($next -ge 0) 'Navigation must target an actual button, not an anonymous wrapper'
        if (!($disabled -band (1 -shl $next))) { break }
      }
      Assert-True (!($disabled -band (1 -shl $next))) 'Navigation cannot skip disabled buttons'
    }
  }
}
Assert-True ($buttons[3].selected -eq 'Player.Paused') 'Play/pause must use a native radio state'
Assert-True ($buttons[1].selected -eq 'Playlist.IsRepeatOne') 'Repeat-one must use a native radio state'
foreach ($state in @('focus', 'nofocus', 'disabled')) {
  Assert-True ($buttons[3].SelectSingleNode('./textureradioon' + $state).InnerText -eq 'osd/nara/play.png') "Paused state must display play: $state"
  Assert-True ($buttons[3].SelectSingleNode('./textureradiooff' + $state).InnerText -eq 'osd/nara/pause.png') "Playing state must display pause: $state"
  Assert-True ($buttons[1].SelectSingleNode('./textureradioon' + $state).InnerText -eq 'osd/nara/repeat-one.png') "Repeat-one icon changed: $state"
  Assert-True ($buttons[1].SelectSingleNode('./textureradiooff' + $state).InnerText -eq 'osd/nara/repeat.png') "Repeat icon changed: $state"
}
Assert-True ($expanded.OuterXml -notmatch 'osdfade|colors/black.png|80141418|SeekTimeLabelVar|MediaFlags') 'Unexpected overlay in expanded player'

$nibs = $expanded.SelectNodes('//control[@type="progress" and contains(righttexture,"progress-nib.png")]')
Assert-True ($nibs.Count -eq 2) 'Exactly one playback nib and one seek nib are allowed'
Assert-True ($nibs[0].info -eq 'Player.Progress' -and $nibs[0].visible -eq '!Player.Seeking') 'Playback nib binding changed'
Assert-True ($nibs[1].info -eq 'Player.SeekBar' -and $nibs[1].visible -eq 'Player.Seeking') 'Seek nib must be mutually exclusive'
$mouseSlider = $expanded.SelectSingleNode('//control[@type="slider"]')
foreach ($name in @('textureslidernib', 'textureslidernibfocus', 'textureslidernibdisabled', 'texturesliderbardisabled')) {
  $texture = $mouseSlider.SelectSingleNode('./' + $name)
  Assert-True ($null -ne $texture -and !$texture.InnerText) "Invisible mouse slider inherits a default texture: $name"
}
Assert-True ($documents['Defaults.xml'].SelectSingleNode('//default[@type="progress"]/overlaytexture').InnerText -eq '') 'A default progress overlay would add a second marker'
$seekGroup = $mouseSlider.ParentNode
Assert-True ([int]$buttonRow.top - ([int]$seekGroup.top + 11) -ge 24) 'Seek bar and buttons need at least 24 pixels of visual separation'
$track = $seekGroup.SelectSingleNode('./control[@type="image"]')
$videoTrack = $documents['VideoOSD.xml'].SelectSingleNode('//control[@id="6000"]/control[@type="image"]')
Assert-True ($track.top -eq $videoTrack.top -and $track.height -eq $videoTrack.height -and $track.texture.OuterXml -eq $videoTrack.texture.OuterXml) 'Music seek track must match video styling'
Assert-True ($seekGroup.SelectNodes('.//*[@material="glass"]').Count -eq 0) 'The seek bar must not use glass'
$fileManagerFanart = $documents['FileManager.xml'].SelectSingleNode('//control[contains(texture,"NaraFileManagerRandomFanartVar")]')
Assert-True ($fileManagerFanart.visible -notmatch 'Player.HasAudio' -and $fileManagerFanart.visible -match 'Player.HasVideo') 'Music startup must retain file manager fanart without changing video gating'

# These modeless windows are drawn after the fullscreen page.
$eligibility = 'Window.IsActive(fullscreenvideo) | [Window.IsActive(visualisation) + PVR.IsPlayingRadio]'
foreach ($name in @('DialogSeekBar.xml', 'Custom_1109_TopBarOverlay.xml')) {
  Assert-True ($documents[$name].SelectSingleNode('/window/visible').InnerText -eq $eligibility) "Legacy overlay is not isolated: $name"
}

$background = $documents['Includes_MusicBackground.xml']
Assert-True ($background.SelectNodes('//control[@type="image"]').Count -eq 1) 'Background must use one image'
Assert-True ($background.SelectNodes('//animation|//control[@type="multiimage" or @type="visualisation" or @type="videowindow"]').Count -eq 0) 'Background must use a single static image'
$backgroundTexture = $background.SelectSingleNode('//texture')
Assert-True (!$backgroundTexture.HasAttribute('material')) 'Music background must use ordinary image rendering'
Assert-True ($backgroundTexture.InnerText -eq '$INFO[Skin.String(Nara.MusicBackground)]' -and $backgroundTexture.background -eq 'true') 'Background must load the saved image asynchronously'
Assert-True ($backgroundTexture.fallback -eq 'osd/nara/music-background.png') 'An empty or unavailable custom image must use the default wallpaper'
# The wallpaper now only exists inside media/Textures.xbt, so its pixels can no longer be
# re-inspected from the skin folder; assert that it is still packed and wired as the fallback.
Assert-True (Test-SkinTexture 'osd/nara/music-background.png') 'The default wallpaper must stay packed in Textures.xbt'

$playlist = $documents['Custom_1114_MusicPlaylistDialog.xml']
Assert-True ($playlist.window.id -eq '1114') 'Music playlist must have an independent dialog ID'
$panel = $playlist.SelectSingleNode('/window/controls/control')
Assert-True ($panel.centerleft -eq '50%' -and $panel.centertop -eq '50%') 'Playlist popup must be centered'
foreach ($layout in $playlist.SelectNodes('//itemlayout | //focusedlayout')) {
  $columns = $layout.SelectNodes('control[@type="label"]')
  Assert-True ($columns.Count -eq 2) 'Playlist must only show title and artist columns'
  Assert-True ([int]$columns[0].left + [int]$columns[0].width -le [int]$columns[1].left -and [int]$columns[1].left + [int]$columns[1].width -le [int]$layout.width) 'Playlist columns must fit without overlap'
}
Assert-True ($controls.SelectSingleNode('//control[@id="70051"]/onclick').InnerText -eq 'ActivateWindow(1114)') 'Music controls must open the music-only playlist'
Assert-True ($playlist.SelectSingleNode('//content').focusplaying -eq 'true') 'Playlist must focus the playing item'
Assert-True ($playlist.SelectSingleNode('//content').InnerText -eq 'playlistmusic://?reload=$INFO[Playlist.Position(music)]') 'Music playlist provider changed'
$panelImages = $includes['NaraMusicPlaylistBackground'].SelectNodes('.//control[@type="image"]')
Assert-True ($panelImages.Count -eq 10) 'Short-playlist panel variants changed'
$referencePanel = $documents['FileManager.xml'].SelectSingleNode('//texture[@material="glass"]')
$referenceFocus = $documents['FileManager.xml'].SelectSingleNode('//focusedlayout/control[texture="lists/focus.png"]')
Assert-True ($referenceFocus.texture.colordiffuse -eq 'glass_focus_medium') 'File Manager and music popup rows must use the shared medium highlight'
for ($i = 0; $i -lt 10; $i++) {
  Assert-True ($panelImages[$i].texture.glassstyle -eq 'regular') 'Every music panel must use regular glass'
  Assert-True ($panelImages[$i].texture.cornerradius -eq $referencePanel.cornerradius) 'Music panel corners must match File Manager'
  Assert-True ([int]$panelImages[$i].top -eq 252 - 28 * $i) 'Short-playlist centering changed'
  if ($i -lt 9) { Assert-True ([int]$panelImages[$i].height -eq 166 + 56 * $i) 'Short-playlist panel height changed' }
  else { Assert-True ($panelImages[$i].bottom -eq '0') 'Full playlist panel must fill its group' }
}
$focus = $playlist.SelectSingleNode('//focusedlayout/control[texture/@colordiffuse="glass_focus_medium"]')
Assert-True ($focus.top -eq $referenceFocus.top -and $focus.bottom -eq $referenceFocus.top) 'Playlist focus must retain 3-pixel vertical padding'
Assert-True ($focus.texture.colordiffuse -eq $referenceFocus.texture.colordiffuse) 'Playlist focus must reuse File Manager color'
Assert-True ($focus.texture.InnerText -eq 'colors/white.png' -and $focus.texture.cornerradius -eq '4' -and !$focus.texture.HasAttribute('border')) 'Short popup rows need a single rounded quad, not overlapping nine-slice borders'
$audio = $documents['Custom_1113_MusicAudioDialog.xml']
Assert-True ($audio.SelectSingleNode('//texture[@material="glass" and @cornerradius="42"]').glassstyle -eq 'regular') 'Audio panel must use regular glass'
$audioFocus = $audio.SelectSingleNode('//control[texture/@colordiffuse="glass_focus_medium"]')
$mute = $audio.SelectSingleNode('//control[@id="11"]')
Assert-True ($audioFocus.texture.OuterXml -eq $focus.texture.OuterXml) 'Audio and playlist popups must use identical seam-free focus'
Assert-True ([int]$audioFocus.top - [int]$mute.top -eq 3 -and [int]$mute.height - [int]$audioFocus.height -eq 6) 'Audio focus must retain 3-pixel vertical padding'
Assert-True ($audioFocus.visible -eq 'Control.HasFocus(11)' -and !$mute.texturefocus.InnerText) 'Mute focus must render once'
$chooseBackground = $audio.SelectSingleNode('//control[@id="12"]')
$resetBackground = $audio.SelectSingleNode('//control[@id="13"]')
Assert-True ($chooseBackground.onclick -eq 'Skin.SetImage(Nara.MusicBackground)') 'Custom background must use the native image browser and persistent skin setting'
Assert-True ($resetBackground.SelectSingleNode('onclick').InnerText -eq 'Skin.Reset(Nara.MusicBackground)') 'Restore must clear only the music background setting'
Assert-True ($resetBackground.enable -eq '!String.IsEmpty(Skin.String(Nara.MusicBackground))' -and $resetBackground.SelectNodes('onclick')[1].InnerText -eq 'SetFocus(12)') 'Restore must return focus to the chooser before becoming disabled'
foreach ($id in @(10, 11, 12, 13)) {
  $row = $audio.SelectSingleNode('//control[@id="' + $id + '"]')
  Assert-True ([int]$row.top + [int]$row.height -le [int]$row.ParentNode.height) "Music setting exceeds dialog bounds: $id"
  foreach ($direction in @('onup', 'ondown')) {
    $target = $row.SelectSingleNode($direction).InnerText
    Assert-True ($null -ne $audio.SelectSingleNode('//control[@id="' + $target + '"]')) "Music setting navigation target missing: $id $direction"
  }
}
$videoPlaylist = $documents['Custom_1112_OSDPlaylistDialog.xml']
Assert-True ($videoPlaylist.OuterXml -notmatch 'NaraMusic|Player.HasAudio|material="glass"') 'Video playlist must not contain music-specific styles'
Assert-True ($videoPlaylist.SelectSingleNode('//content').InnerText -eq 'playlistvideo://?reload=$INFO[Playlist.Position(video)]') 'Video playlist provider must stay unchanged'
Assert-True ($null -eq $documents['Includes_DialogSelect.xml'].SelectSingleNode('//include[@name="NaraStreamDialogPanel"]')) 'Shared video dialog must not contain a music glass branch'

foreach ($name in @('Custom_1114_MusicPlaylistDialog.xml', 'Custom_1113_MusicAudioDialog.xml')) {
  $popup = [xml]$documents[$name].OuterXml
  Expand-Includes $popup.window
  Assert-True (!$popup.OuterXml.Contains('$PARAM[')) "Unresolved popup parameter: $name"
  $ids = @($popup.SelectNodes('//control[@id]'))
  Assert-True (@($ids | Group-Object { $_.GetAttribute('id') } | Where-Object Count -gt 1).Count -eq 0) "Duplicate popup IDs: $name"
}
Assert-True ($documents['Custom_1113_MusicAudioDialog.xml'].OuterXml -notmatch 'colors/black.png|osdfade') 'Music audio popup must be glass without a black scrim'

Write-Output "PASS: $($documents.Count) XML files; music layout/packed assets, fused CU-LRC lyric column, expanded controls/popups, legacy overlay isolation, single nib, custom static background, regular glass and independent video dialog checked."
