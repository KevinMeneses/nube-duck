-- CPU: renderiza 20 s de material real (4 canales) sin plugin, con claude_duck_band, con Nube Duck (1 banda)
-- y con Nube Duck en el peor caso (4 bandas, M/S, voz por banda). Escribe tests/out/perf.txt.
local OUT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/out"
local SIG = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$") .. "/signals/real.wav"
local f = io.open(OUT .. "/perf.txt", "w")
local PREV = reaper.EnumProjects(-1)
reaper.Main_OnCommand(40859, 0)
local TAB = OUT .. "/_tab_perf.rpp"; reaper.Main_SaveProjectEx(0, TAB, 0); reaper.Main_openProject("noprompt:" .. TAB)
local P = reaper.EnumProjects(-1)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(P, 0)
reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", 4)
local item = reaper.AddMediaItemToTrack(tr); local take = reaper.AddTakeToMediaItem(item)
local src = reaper.PCM_Source_CreateFromFile(SIG); reaper.SetMediaItemTake_Source(take, src)
reaper.SetMediaItemInfo_Value(item, "D_LENGTH", reaper.GetMediaSourceLength(src))
local function render(name, fxname, nfx, setup)
  reaper.SelectProjectInstance(P)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  for k = 1, nfx do local fx = reaper.TrackFX_AddByName(tr, fxname, false, -1); setup(fx) end
  os.remove(OUT .. "/" .. name .. ".wav")
  reaper.GetSetProjectInfo(P, "RENDER_SETTINGS", 0, true); reaper.GetSetProjectInfo(P, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo(P, "RENDER_CHANNELS", 2, true)
  reaper.GetSetProjectInfo_String(P, "RENDER_FILE", OUT, true); reaper.GetSetProjectInfo_String(P, "RENDER_PATTERN", name, true)
  reaper.SelectProjectInstance(P)
  local t0 = reaper.time_precise(); reaper.Main_OnCommand(42230, 0); return reaper.time_precise() - t0
end
local N = 8   -- instancias en serie para que el tiempo se pueda medir
local t0 = render("perf_vacio", "", 0, function() end)
local t1 = render("perf_orig", "JS:Nube Duck/_prueba_orig_fix.jsfx", N, function() end)
local t2 = render("perf_duck1", "JS:Nube Duck/nube_duck.jsfx", N, function() end)
local t3 = render("perf_duck4", "JS:Nube Duck/nube_duck.jsfx", N, function(fx)
  for b = 0, 3 do local o = 7 + 13 * b   -- parámetro = posición del slider (banda b: estado, +4 canal)
    reaper.TrackFX_SetParam(tr, fx, o, 1); reaper.TrackFX_SetParam(tr, fx, o + 4, 1 + b % 2)
  end
end)
local L = reaper.GetMediaSourceLength(src)
local function pct(t) return 100 * (t - t0) / N / L end
f:write(string.format("%d instancias, %.0f s de audio: vacio %.2f s | original (1e-12 corregido) %.2f s (%.2f %%/inst) | Nube Duck 1 banda %.2f s (%.2f %%) | 4 bandas M/S %.2f s (%.2f %%)\n",
  N, L, t0, t1, pct(t1), t2, pct(t2), t3, pct(t3)))
reaper.SelectProjectInstance(P); reaper.Main_SaveProject(P, false); reaper.Main_OnCommand(40860, 0)
if PREV and PREV ~= P and reaper.ValidatePtr(PREV, "ReaProject*") then reaper.SelectProjectInstance(PREV) end
f:write("done\n"); f:close()
