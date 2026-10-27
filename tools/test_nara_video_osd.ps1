param([string]$SkinDirectory = (Join-Path $PSScriptRoot '..'))

$ErrorActionPreference = 'Stop'

function Assert-True([bool]$Condition, [string]$Message) {
  if (!$Condition) { throw $Message }
}

$documents = @{}
$includes = @{}
$variables = @{}
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $SkinDirectory 'xml') -Filter '*.xml') {
  $document = [xml](Get-Content -Raw -LiteralPath $file.FullName)
  $documents[$file.Name] = $document
  foreach ($node in $document.SelectNodes('/includes/include[@name]')) { $includes[$node.GetAttribute('name')] = $node }
  foreach ($node in $document.SelectNodes('/includes/variable[@name]')) { $variables[$node.GetAttribute('name')] = $node }
}

$osd = $documents['VideoOSD.xml']
$header = $includes['VideoOSDHeader']
$shelf = $documents['Custom_1116_OSDPlaylistShelf.xml']
$processInfo = $documents['DialogPlayerProcessInfo.xml']
$fullscreenInfo = $documents['DialogFullScreenInfo.xml']
$seekBar = $documents['DialogSeekBar.xml']
$redirect = @($fullscreenInfo.SelectNodes('/window/onload'))
Assert-True ($redirect.Count -eq 2 -and $redirect[0].InnerText -eq 'Dialog.Close(fullscreeninfo,true)' -and $redirect[1].InnerText -eq 'ActivateWindow(playerprocessinfo)') 'Fullscreen Info must close its transparent window before opening process info'
foreach ($action in $redirect) {
  Assert-True ($action.condition -eq '!VideoPlayer.Content(LiveTV)') 'Fullscreen Info redirection must preserve live-TV programme information'
}
Assert-True (!$seekBar.OuterXml.Contains('VideoPlayer.Tagline') -and !$seekBar.OuterXml.Contains('$VAR[NowPlayingPosterVar]')) 'The old movie synopsis panel must be removed'
Assert-True ($null -ne $seekBar.SelectSingleNode('//control[@id="401"]') -and $null -ne $seekBar.SelectSingleNode('//control[@id="403"]')) 'Seek progress controls must remain available'
Assert-True ($seekBar.OuterXml.Contains('$INFO[PVR.EpgEventIcon]')) 'Live-TV programme information must be preserved'
Assert-True ($seekBar.OuterXml.Contains('$INFO[VideoPlayer.NextTitle,: ]') -and !$variables.ContainsKey('OSDNextLabelVar')) 'Keep the live-TV next programme without unused playlist branches'
foreach ($name in @('NaraVideoOSDButton', 'NaraVideoOSDPlayButton')) {
  $action = $includes[$name].SelectSingleNode('oninfo')
  Assert-True ($action.InnerText -eq 'ActivateWindow(playerprocessinfo)' -and $action.condition -eq '!VideoPlayer.Content(LiveTV)') "OSD button Info action missing: $name"
}
foreach ($control in $osd.SelectNodes('//control[@type="button"]')) {
  $action = $control.SelectSingleNode('oninfo')
  Assert-True ($action.InnerText -eq 'ActivateWindow(playerprocessinfo)' -and $action.condition -eq '!VideoPlayer.Content(LiveTV)') 'OSD background and seek-bar focus must route Info to process info'
}
foreach ($control in $osd.SelectNodes('//control[@type="radiobutton"]')) {
  Assert-True ($null -ne $control.SelectSingleNode('include[@content="NaraVideoOSDButton" or text()="NaraVideoOSDPlayButton"]')) 'Every OSD button must inherit the Info action'
}
Assert-True ($osd.SelectSingleNode('//control[@type="slider"][info="Player.Progress"]/oninfo').InnerText -eq 'ActivateWindow(playerprocessinfo)') 'The seek slider must route Info to process info'
$closeInfo = $processInfo.SelectSingleNode('//control[@id="9000"]/oninfo')
Assert-True ($closeInfo.InnerText -eq 'Dialog.Close(playerprocessinfo)' -and $closeInfo.condition -eq 'Player.HasVideo') 'Pressing Info again during video playback must close process info'
Assert-True ($null -ne $documents['Includes.xml'].SelectSingleNode('/includes/include[@file="Includes_VideoOSD.xml"]')) 'OSD includes not registered'
Assert-True ($null -ne $osd.SelectSingleNode('/window/controls/include[text()="VideoOSDHeader"]')) 'OSD header missing'

foreach ($name in @('Includes_VideoOSD.xml', 'VideoOSD.xml', 'Custom_1116_OSDPlaylistShelf.xml')) {
  $document = $documents[$name]
  foreach ($node in $document.SelectNodes('//include[not(@name) and not(@file)]')) {
    $reference = if ($node.HasAttribute('content')) { $node.GetAttribute('content') } else { $node.InnerText.Trim() }
    Assert-True ($includes.ContainsKey($reference)) "Unknown include: $reference"
  }
  foreach ($match in [regex]::Matches($document.OuterXml, '\$VAR\[([^,\]]+)')) {
    Assert-True ($variables.ContainsKey($match.Groups[1].Value)) "Unknown variable: $($match.Groups[1].Value)"
  }
}

$video = '$INFO[Player.Process(videowidth)]×$INFO[Player.Process(videoheight)]'
$fps = '$INFO[Player.Process(videofps),, FPS]'
$audio = '$MAP[NaraTechnicalAudioCodecTextMap,VideoPlayer.AudioCodec]'
$channels = '$INFO[VideoPlayer.AudioChannels(DefaultLayout)]'
foreach ($value in @('$INFO[Player.Process(videowidth)]', '$INFO[Player.Process(videoheight)]', $fps)) {
  Assert-True ($header.OuterXml.Contains($value)) "Header lost the existing process-info field: $value"
  Assert-True ($processInfo.OuterXml.Contains($value)) "Field differs from process-info dialog: $value"
}
Assert-True (!$header.OuterXml.Contains('hdroutputmode') -and !$header.OuterXml.Contains('hdrconversion')) 'Conversion details must not appear in the OSD header'
Assert-True ($processInfo.OuterXml.Contains('Player.Process(hdroutputmode)') -and $processInfo.OuterXml.Contains('Player.Process(hdrconversion)')) 'Process-info conversion details must remain available'
$hdrValues = @($variables['VideoOSDHdrTypeVar'].SelectNodes('value'))
Assert-True ($hdrValues.Count -eq 3 -and $hdrValues[0].condition -eq '!String.IsEmpty(Player.Process(hdrsource))' -and $hdrValues[0].InnerText -eq '$INFO[Player.Process(hdrsource)]') 'HDR badge must prefer the detected source type, including HDR Vivid'
Assert-True ($hdrValues[1].condition -eq '!String.IsEmpty(VideoPlayer.HdrType)' -and $hdrValues[1].InnerText -eq '$MAP[NaraTechnicalHdrTextMap,VideoPlayer.HdrType]' -and $hdrValues[2].InnerText -eq 'SDR') 'HDR badge must reuse the detail-page map with an SDR fallback'
foreach ($name in @('NaraTechnicalHdrTextMap', 'NaraTechnicalAudioCodecTextMap')) {
  Assert-True ($null -ne $documents['Includes_VideoTechnicalFlags.xml'].SelectSingleNode("/includes/map[@name='$name']")) "Shared technical map missing: $name"
}
Assert-True (!$header.OuterXml.Contains('$INFO[Player.FinishTime]')) 'Finish time must not appear in the header'
Assert-True ($header.SelectSingleNode('control/control[@type="image"]/texture').colordiffuse -eq '5AFFFFFF') 'Header gradient opacity must be halved'
$leftHeader = $header.SelectSingleNode('control/control[@type="grouplist"][left]')
$rightHeader = $header.SelectSingleNode('control/control[@type="grouplist"][right]')
Assert-True ($leftHeader.left -eq '30' -and $leftHeader.top -eq '30') 'Left header padding must be 30px'
Assert-True ($rightHeader.right -eq '30' -and $rightHeader.top -eq '30') 'Right header padding must be 30px'
Assert-True ($rightHeader.orientation -eq 'horizontal' -and $rightHeader.align -eq 'right' -and $rightHeader.height -eq '36') 'Technical badges must occupy one right-aligned row'
$badges = @($rightHeader.SelectNodes('include[@content="VideoOSDInfoBadge"]'))
$expectedLabels = @('$VAR[VideoOSDHdrTypeVar]', $video, $fps, $audio, $channels)
Assert-True ($badges.Count -eq 5 -and $rightHeader.SelectNodes('control').Count -eq 0) 'Only the five requested technical badges may appear at the top right'
$maxWidth = ($badges.Count - 1) * [int]$rightHeader.itemgap
for ($index = 0; $index -lt $badges.Count; $index++) {
  Assert-True ($badges[$index].SelectSingleNode('param[@name="label"]').value -eq $expectedLabels[$index]) 'Technical badge fields or order changed'
  $maxWidth += [int]$badges[$index].SelectSingleNode('param[@name="maxwidth"]').value
}
Assert-True ($maxWidth -le [int]$rightHeader.width) 'Technical badges can overflow with long labels'
Assert-True ([int]$badges[0].SelectSingleNode('param[@name="maxwidth"]').value -ge 200) 'Dolby Vision needs enough width for bold uppercase text and both text insets'
Assert-True ([int]$leftHeader.left + [int]$leftHeader.width -lt 1920 - [int]$rightHeader.right - [int]$rightHeader.width) 'Technical badges overlap the title area'
$badge = $includes['VideoOSDInfoBadge'].SelectSingleNode('definition/control')
$detailBadge = $includes['NaraTechnicalTextPill'].SelectSingleNode('definition/control')
Assert-True ($badge.GetAttribute('type') -eq 'button' -and $badge.enable -eq 'false') 'Auto-width badges must never accept OSD focus'
Assert-True ($badge.width.InnerText -eq 'auto' -and $badge.width.max -eq '$PARAM[maxwidth]') 'Badges must size to their labels with bounded width'
$badgeFont = $documents['Font.xml'].SelectSingleNode("/fonts/fontset/font[name='$($badge.font)']")
Assert-True ($badgeFont.size -eq '19' -and $badge.height -eq $detailBadge.height -and $badge.textoffsetx -eq $detailBadge.textoffsetx -and $badge.label -eq '[B][UPPERCASE]$PARAM[label][/UPPERCASE][/B]') 'OSD badges must use 19px bold text while preserving detail-page height and padding'
Assert-True ($badge.disabledcolor -eq $badge.textcolor -and $badge.texturenofocus.colordiffuse -eq 'C0EDEDED' -and $badge.texturenofocus.cornerradius -eq '4') 'Badges must use the softer pale surface and readable dark text while disabled'
$logo = $leftHeader.SelectSingleNode('control[@type="image"]')
$title = $leftHeader.SelectSingleNode('control[@type="label"]')
Assert-True ($logo.texture -eq '$VAR[PlayerClearLogoVar]') 'Logo must reuse the playing-item artwork variable'
Assert-True ($logo.width -eq '356' -and $logo.height -eq '100' -and $logo.aspectratio.InnerText -eq 'keep') 'Clearlogo must fit a 356x100 area without stretching'
Assert-True ($logo.visible -eq '!String.IsEmpty(Player.Art(tvshow.clearlogo)) | !String.IsEmpty(Player.Art(clearlogo))') 'Logo must require available artwork'
Assert-True ($title.visible -eq 'String.IsEmpty(Player.Art(tvshow.clearlogo)) + String.IsEmpty(Player.Art(clearlogo))') 'Title must be the fallback for missing artwork'
Assert-True ($title.label -eq '$VAR[NowPlayingBreadcrumbsVar]') 'Fallback title changed'

$buttons = $osd.SelectSingleNode('//control[@id="201"]')
$down = @($buttons.SelectNodes('ondown'))
Assert-True ($down.Count -eq 2) 'Missing conditional playlist navigation'
Assert-True ($down[0].InnerText -eq 'Nara.OSDPlaylistShelf') 'Down must use the same shelf entry as the shortcut'
Assert-True ($down[0].GetAttribute('condition') -eq 'Integer.IsGreater(Playlist.Length(video),1) + !VideoPlayer.Content(livetv)') 'Playlist entry must require multiple non-live items'
Assert-True ($down[1].InnerText -eq 'noop') 'Single-item playback must not open a shelf'
Assert-True ($buttons.SelectSingleNode('onup').InnerText -eq '87') 'Seek navigation changed'
Assert-True ($buttons.SelectSingleNode('top').InnerText -eq '68') 'Button row moved'
$bottomBar = $osd.SelectSingleNode('//control[@id="200"]/..')
Assert-True ($bottomBar.SelectSingleNode('bottom').InnerText -eq '0') 'Bottom bar moved'
Assert-True ($bottomBar.SelectSingleNode('height').InnerText -eq '142') 'Bottom bar resized'
Assert-True (!$bottomBar.OuterXml.Contains('$VAR[NaraAudioTrackNameVar]') -and !$bottomBar.OuterXml.Contains('$VAR[NaraSubtitleDescriptionVar]')) 'Track descriptions must not appear beside the OSD buttons'
$finishTime = $bottomBar.SelectSingleNode('control[@type="label"][contains(label,"Player.FinishTime")]')
Assert-True ($null -ne $finishTime) 'Estimated finish time missing from the bottom bar'
Assert-True ($finishTime.right -eq '30' -and $finishTime.align -eq 'right') 'Finish time must be aligned to the right edge'
Assert-True ($finishTime.top -eq $buttons.top -and $finishTime.height -eq $buttons.height -and $finishTime.aligny -eq 'center') 'Finish time must align with the button row'
Assert-True ($finishTime.visible -eq '!Player.Paused + !VideoPlayer.Content(livetv) + Integer.IsGreater(Player.Duration(secs),0)') 'Finish-time visibility changed'
Assert-True ($osd.SelectSingleNode('//control[@id="6000"]/top').InnerText -eq '37') 'Progress bar moved'
Assert-True ($osd.SelectSingleNode('//control[@id="70042"]/onclick').InnerText -eq 'ActivateWindow(1112)') 'Existing playlist button changed'
foreach ($name in @('NaraVideoOSDButton', 'NaraVideoOSDPlayButton')) {
  $buttonStyle = $includes[$name]
  Assert-True ($buttonStyle.texturefocus.colordiffuse -eq '$VAR[VideoOSDButtonFocusSurfaceVar]') 'OSD button focus background must follow shelf visibility'
  foreach ($texture in @('textureradioonfocus', 'textureradioofffocus')) {
    Assert-True ($buttonStyle.SelectSingleNode($texture).colordiffuse -eq '$VAR[VideoOSDButtonFocusForegroundVar]') 'Focused OSD icons must return to their normal color under the shelf'
  }
}
foreach ($entry in @(@('VideoOSDButtonFocusSurfaceVar', '00FFFFFF', 'focus_surface'), @('VideoOSDButtonFocusForegroundVar', 'text_primary', 'focus_foreground'))) {
  $values = @($variables[$entry[0]].SelectNodes('value'))
  Assert-True ($values.Count -eq 2 -and $values[0].condition -eq 'Window.IsVisible(1116)' -and $values[0].InnerText -eq $entry[1] -and !$values[1].HasAttribute('condition') -and $values[1].InnerText -eq $entry[2]) 'OSD focus colors must restore when the shelf closes'
}

Assert-True ($shelf.window.GetAttribute('type') -eq 'dialog') 'Shelf must preserve the underlying OSD'
Assert-True ($shelf.window.defaultcontrol.InnerText -eq '6') 'Shelf must focus the playlist'
$list = $shelf.SelectSingleNode('//control[@id="6"]')
Assert-True ($list.orientation -eq 'horizontal') 'Playlist is not horizontal'
Assert-True ($list.GetAttribute('type') -eq 'list' -and $list.defaultfocusposition -eq '1') 'Queue must use a normal list with the playing item initially in the second slot'
Assert-True ($null -eq $list.focusposition -and $null -eq $list.movement) 'Queue navigation must not pin the focus to a fixed slot'
$up = @($list.SelectNodes('onup'))
Assert-True ($up.Count -eq 3 -and $up[0].InnerText -eq 'ClearProperty(VideoOSDPlaylist.CloseOSD,1116)' -and $up[2].InnerText -eq 'Dialog.Close(1116)') 'Up must retain the OSD and close the shelf'
Assert-True ($up[1].InnerText -eq 'SetProperty(VideoOSDPlaylist.FocusControl,201,1116)') 'Up must request focus on the button row'
$shelfDown = @($list.SelectNodes('ondown'))
Assert-True ($shelfDown.Count -eq 3 -and $shelfDown[0].InnerText -eq $up[0].InnerText -and $shelfDown[2].InnerText -eq $up[2].InnerText) 'Down must retain the OSD and close the shelf'
Assert-True ($shelfDown[1].InnerText -eq 'SetProperty(VideoOSDPlaylist.FocusControl,87,1116)') 'Down must request focus on the seek bar without seeking'
Assert-True ($osd.SelectSingleNode('//control[@id="87"]/ondown').InnerText -eq '200') 'Down from the seek bar must lead to the OSD buttons'
Assert-True ($list.onback -eq 'Dialog.Close(1116)') 'Back must close the shelf'
$unload = @($shelf.SelectNodes('/window/onunload'))
Assert-True ($unload.Count -eq 4 -and $unload[0].InnerText -eq 'Dialog.Close(videoosd)') 'Shelf must restore the OSD on close'
Assert-True ($unload[0].GetAttribute('condition') -eq 'String.IsEqual(Window(1116).Property(VideoOSDPlaylist.CloseOSD),true)') 'Only an OSD opened by the shelf should close on cancel'
Assert-True ($unload[1].InnerText -eq 'SetFocus($INFO[Window(1116).Property(VideoOSDPlaylist.FocusControl)])' -and $unload[1].GetAttribute('condition') -eq '!String.IsEmpty(Window(1116).Property(VideoOSDPlaylist.FocusControl))') 'Shelf must focus the requested OSD control only after it closes'
Assert-True ($unload[2].InnerText -eq 'ClearProperty(VideoOSDPlaylist.CloseOSD,1116)' -and $unload[3].InnerText -eq 'ClearProperty(VideoOSDPlaylist.FocusControl,1116)') 'Shelf must clear its close and focus state'
Assert-True ($list.content.InnerText -eq 'playlistvideo://?reload=$INFO[Playlist.Position(video)]') 'Shelf must use the current queue'
Assert-True ($list.content.GetAttribute('focusplaying') -eq 'true') 'Current item is not the default focus'
Assert-True ($list.content.GetAttribute('loaditemdetails') -ne 'false') 'Playlist artwork loading disabled'
Assert-True (!$list.content.HasAttribute('sortby')) 'Playlist order must not be changed'
foreach ($window in @($shelf, $documents['Custom_1112_OSDPlaylistDialog.xml'])) {
  $click = @($window.SelectNodes('//control[@id="6"]/onclick'))
  Assert-True ($click.Count -eq 3) 'Selection must play, close its dialog and close the OSD'
  Assert-True ($click[0].InnerText -eq 'Playlist.PlayPosition(video,$INFO[ListItem.Property(playlistposition)])') 'Playback must use the existing queue position without requesting resume'
  Assert-True ($click[0].GetAttribute('condition') -eq '!ListItem.IsPlaying') 'Current item must not restart'
  Assert-True ($click[1].InnerText -eq "Dialog.Close($($window.window.id))") 'Selection must close its dialog'
  Assert-True ($click[2].InnerText -eq 'Dialog.Close(videoosd)' -and !$click[2].HasAttribute('condition')) 'Selection must close the OSD even for the current item'
}
Assert-True ($list.ParentNode.SelectSingleNode('bottom').InnerText -eq $bottomBar.SelectSingleNode('height').InnerText) 'Shelf overlaps the bottom bar'
$card = $includes['VideoOSDPlaylistCard'].SelectSingleNode('definition/control')
Assert-True ([int]$list.top + [int]$list.height -le [int]$list.ParentNode.SelectSingleNode('height').InnerText) 'Playlist exceeds the shelf bounds'
Assert-True ([int]$card.top + [int]$card.height -le [int]$list.height) 'Playlist cards are clipped vertically'
$shelfHeight = [int]$list.ParentNode.SelectSingleNode('height').InnerText
Assert-True ($shelfHeight -eq 230 -and $list.ParentNode.SelectSingleNode('control[@type="image"]/height').InnerText -eq '230') 'Playlist background must shrink to 230px without the heading'
Assert-True ($shelfHeight - [int]$list.top - [int]$card.top - [int]$card.height -eq 15) 'Playlist card distance from the seek bar changed'
Assert-True ($null -eq $list.ParentNode.SelectSingleNode('control[@type="label"]')) 'Playlist heading must be removed'
Assert-True ([int]$list.top + [int]$card.top -eq 15) 'Playlist cards must have 15px top padding without a heading gap'
Assert-True ([int]$card.top + [int]$card.height + 14 -le [int]$list.height) 'Enlarged card focus glow is clipped at the bottom'
$cardStep = [int]$list.itemlayout.width
Assert-True ($cardStep -eq [int]$list.focusedlayout.width -and $cardStep - [int]$card.width -eq 20) 'Normal and focused card spacing must remain 20px'
Assert-True ([int]$list.left + [int]$card.left -eq 30 -and 1920 - ([int]$list.left + 4 * $cardStep + [int]$card.left + [int]$card.width) -eq 30) 'Five cards must have 30px outer margins'
Assert-True ([int]$list.width -eq 5 * $cardStep) 'Shelf must fit five enlarged cards'
$playingIcon = $card.SelectSingleNode('control[@type="image"][texture="osd/nara/play-circle.png"]')
Assert-True ($playingIcon.visible -eq 'ListItem.IsPlaying' -and $playingIcon.texture.colordiffuse -eq 'B3FFFFFF') 'Current-item marker must use the translucent circle-play icon'
Assert-True ($playingIcon.centerleft -eq '50%' -and $playingIcon.centertop -eq '50%') 'Current-item marker must be centered on the image'
Assert-True (Test-Path -LiteralPath (Join-Path $SkinDirectory "media/$($playingIcon.texture.InnerText)")) 'Current-item icon asset missing'
Assert-True ($card.SelectNodes('control[@type="image"][visible="ListItem.IsPlaying"]').Count -eq 1) 'Current item must have only its playing icon, without a black overlay'
Assert-True ($card.width -eq '356' -and $card.height -eq '200') 'Card image must use the reclaimed side margins'
$cardTitle = $card.SelectSingleNode('control[@type="label"][label="$VAR[VideoOSDPlaylistTitleVar]"]')
$cardDuration = $card.SelectSingleNode('control[@type="label"][label="$INFO[ListItem.Duration]"]')
$cardPlaying = $card.SelectSingleNode('control[@type="label"][label="$LOCALIZE[31000]"]')
Assert-True ($cardTitle.textcolor -eq 'text_secondary' -and $cardDuration.textcolor -eq 'text_secondary') 'Card text must use subdued colors'
Assert-True ($cardDuration.visible -eq '!ListItem.IsPlaying' -and $cardPlaying.visible -eq 'ListItem.IsPlaying' -and $cardPlaying.textcolor -eq 'FFFFFFFF') 'Bright now-playing text must replace the current item duration'
Assert-True ($cardDuration.top -eq '161' -and $cardDuration.right -eq '12' -and $cardDuration.align -eq 'right') 'Duration must be in the image bottom-right corner'
foreach ($field in @('right', 'top', 'width', 'height', 'font', 'align')) {
  Assert-True ($cardPlaying.SelectSingleNode($field).InnerText -eq $cardDuration.SelectSingleNode($field).InnerText) 'Duration and now-playing text must occupy the same space'
}
Assert-True ([int]$cardTitle.left + [int]$cardTitle.width -lt [int]$card.width - [int]$cardDuration.right - [int]$cardDuration.width) 'Card title overlaps the duration'
foreach ($label in $card.SelectNodes('control[@type="label"]')) {
  Assert-True ([int]$label.top + [int]$label.height -le [int]$card.height) 'Card text extends below the image'
  Assert-True ($label.selectedcolor -eq $label.textcolor) 'Playing-item selection must not override card text colors'
}

$repositoryDirectory = (Resolve-Path (Join-Path $SkinDirectory '../..')).Path
$playerInfo = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/guilib/guiinfo/PlayerGUIInfo.cpp')
foreach ($dimension in @(@('VIDEOWIDTH', 'Width'), @('VIDEOHEIGHT', 'Height'))) {
  Assert-True ($playerInfo -match "case PLAYER_PROCESS_$($dimension[0]):\s*value = std::to_string\(CServiceBroker::GetDataCacheCore\(\).GetVideo$($dimension[1])\(\)\);") 'Video dimensions must not contain locale-dependent thousands separators'
}
$controlFactory = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/guilib/GUIControlFactory.cpp')
Assert-True ($controlFactory -match 'XMLUtils::GetInt\(pControlNode, "defaultfocusposition", defaultFocusPosition\)\)\s*lcontrol->SetDefaultFocusPosition\(defaultFocusPosition\)') 'List default focus position must be read from the skin'
$baseContainer = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/guilib/GUIBaseContainer.cpp')
Assert-True ($baseContainer.Contains('SelectDefaultItem(defaultItem);') -and $baseContainer.Contains('SelectDefaultItem(m_listProvider->GetDefaultItem());')) 'Both asynchronous loading and reopening must apply the default focus position'
$windowManager = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/guilib/GUIWindowManager.cpp')
Assert-True ($windowManager -match 'action.GetID\(\) == ACTION_MOVE_DOWN && action.GetHoldTime\(\) > 0 &&\s*\(dialog->GetID\(\) == WINDOW_HOME \+ 1116 \|\|\s*\(dialog->GetID\(\) == WINDOW_DIALOG_VIDEO_OSD &&\s*\(dialog->GetFocusedControlID\(\) == 87 \|\| dialog->ControlGroupHasFocus\(201, 0\)\)\)\)') 'Held Down must not skip the seek bar or cycle back to the shelf'
Assert-True ($windowManager -match 'if \(skin && skin->HasSkinFile\("Custom_1116_OSDPlaylistShelf.xml"\)\)\s*return true;') 'Down-repeat suppression must require the queue-card skin'
$provider = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/guilib/listproviders/DirectoryProvider.h')
Assert-True ($provider -match 'bool AlwaysFocusDefaultItem\(\) const override\s*\{ return m_focusPlayingItem; \}') 'Reopened playlists must focus the current item rather than restoring the previous selection'
Assert-True ($provider -match 'bool FocusDefaultItemOnUpdate\(\) const override\s*\{ return m_focusPlayingItem; \}') 'Asynchronously loaded playlists must still focus the current item'
$settings = [xml](Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'system/settings/android.xml'))
$binding = $settings.SelectSingleNode('//group[@id="nara.general.keymaps"]/setting[@id="nara.input.osdkeymap.playlistshelf"]')
Assert-True ($null -ne $binding -and $binding.label -eq '70192' -and $binding.help -eq '70193') 'Independent shelf setting missing from the general key-mapping group'
$keymap = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/application/ApplicationNaraKeymapHandling.cpp')
$callbacks = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/application/ApplicationSettingsHandling.cpp')
$builtins = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory 'xbmc/interfaces/builtins/GUIBuiltins.cpp')
Assert-True ($callbacks.Contains('CSettings::SETTING_NARA_INPUT_OSDKEYMAP_PLAYLISTSHELF')) 'Shelf setting callback not registered'
Assert-True ($keymap.Contains('{CSettings::SETTING_NARA_INPUT_OSDKEYMAP_PLAYLISTSHELF, "Nara.OSDPlaylistShelf"}')) 'Shelf action not registered for capture and conflict checks'
Assert-True ($keymap -match '"window11116",\s*\{\{settings.GetString\(CSettings::SETTING_NARA_INPUT_OSDKEYMAP_PLAYLISTSHELF\), "Back"\}\}') 'Shelf shortcut must close through Back'
Assert-True ($keymap.Contains('"FullscreenVideo", videoMappings, true') -and $keymap.Contains('"VideoOSD", videoMappings)')) 'Up/Down must remain restricted to fullscreen video'
Assert-True ($builtins.Contains('"nara.osdplaylistshelf"')) 'Shelf builtin not registered'
Assert-True ($builtins.Contains('shelf->SetProperty("VideoOSDPlaylist.CloseOSD", !osd->IsDialogRunning());')) 'Shelf must remember whether it opened the OSD'
Assert-True ($builtins -match 'osd->Open\(false\);\s*shelf->Open\(false\);') 'OSD must open without blocking the shelf'
Assert-True ($builtins.Contains('topmostDialog != WINDOW_INVALID && topmostDialog != WINDOW_DIALOG_VIDEO_OSD')) 'Shelf must not open over another modal dialog'
foreach ($language in @('en_gb', 'zh_cn')) {
  $strings = Get-Content -Raw -LiteralPath (Join-Path $repositoryDirectory "addons/resource.language.$language/resources/strings.po")
  foreach ($id in @($binding.label, $binding.help)) {
    Assert-True ([regex]::Matches($strings, "(?m)^msgctxt `"#$id`"\r?$").Count -eq 1) "Missing or duplicated $language string: $id"
  }
}

Write-Output "PASS: $($documents.Count) skin XML files parsed; OSD fields, geometry, playlist navigation, close actions and shortcut wiring checked."
