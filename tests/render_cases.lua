-- Renderiza los casos de tests/out/cases.txt (los escribe cases.py) en una pestaña propia y la cierra.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
-- Puede haber otras sesiones usando el mismo REAPER: se guarda el puntero de la pestaña propia, se usa en todas
-- las llamadas y se vuelve a activar antes de cada render; al final se cierra SOLO esa pestaña.
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

local FX = {duck = "JS:Nube Duck/nube_duck.jsfx", orig = "JS:Claude/claude_duck_band.jsfx",
            orig_ni = "JS:Nube Duck/_prueba_orig_fix.jsfx"}   -- el original con 1e-12 escrito como 0.000000000001 (solo pruebas)
-- índice de parámetro = posición del slider en la declaración (Nube Duck salta de 7 a 11)
local function pidx(fxk, sl) if fxk == "duck" and sl > 7 then return sl - 4 end return sl - 1 end
-- sliders con forma :log=mid (REAPER los expone normalizados 0..1): desde/hasta, ataque, release de cada banda
local function logspec(s)
  if s < 11 or s > 62 then return nil end
  local p = (s - 11) % 13
  if p == 2 or p == 3 then return {20, 20000, 1000} end
  if p == 10 then return {0.5, 200, 10} end
  if p == 11 then return {10, 2000, 200} end
end
local function to_norm(spec, v)
  local mn, mx, mid = spec[1], spec[2], spec[3]
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end

local only = nil
local fo = io.open(OUT .. "/only.txt"); if fo then only = fo:read("l"); fo:close() end
local CASES = {}
for line in io.lines(OUT .. "/cases.txt") do
  local name, sig, fx, params = line:match("^([^;]*);([^;]*);([^;]*);(.*)$")
  if not only or only == "" or name:match(only) then
    local ps = {}
    for k, v in params:gmatch("(%d+)=([^,]+)") do ps[#ps + 1] = {tonumber(k), tonumber(v)} end
    CASES[#CASES + 1] = {name, sig, fx, ps}
  end
end

local PREV = reaper.EnumProjects(-1)
reaper.Main_OnCommand(40859, 0) -- pestaña nueva
local TAB = OUT .. "/_tab_render.rpp"
reaper.Main_SaveProjectEx(0, TAB, 0)
reaper.Main_openProject("noprompt:" .. TAB)
local P = reaper.EnumProjects(-1)
reaper.GetSetProjectInfo(P, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(P, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(P, 0)
reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", 4)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 0)
reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN_AUTO", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN_AUTO", 0)

for _, c in ipairs(CASES) do
  local name, sig, fxk, params = c[1], c[2], c[3], c[4]
  reaper.SelectProjectInstance(P)
  local s = reaper.PCM_Source_CreateFromFile(ROOT .. "/signals/" .. sig)
  reaper.SetMediaItemTake_Source(take, s)
  reaper.SetMediaItemInfo_Value(item, "D_LENGTH", reaper.GetMediaSourceLength(s))
  reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 0); reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 0)
  reaper.UpdateItemInProject(item)
  while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
  local fx = reaper.TrackFX_AddByName(tr, FX[fxk], false, -1)
  if fx < 0 then log("ERROR no cargó el FX", FX[fxk]) break end
  for _, pv in ipairs(params) do
    local sl, v = pv[1], pv[2]
    local spec = fxk == "duck" and logspec(sl)
    if spec then reaper.TrackFX_SetParamNormalized(tr, fx, pidx(fxk, sl), to_norm(spec, v))
    else reaper.TrackFX_SetParam(tr, fx, pidx(fxk, sl), v) end
  end
  local file = OUT .. "/" .. name .. ".wav"
  os.remove(file)
  reaper.GetSetProjectInfo_String(P, "RENDER_FORMAT", "ZXZhdyAAAQ==", true)   -- WAV 32 bit float
  reaper.GetSetProjectInfo(P, "RENDER_SETTINGS", 0, true)
  reaper.GetSetProjectInfo(P, "RENDER_BOUNDSFLAG", 1, true)
  reaper.GetSetProjectInfo(P, "RENDER_SRATE", 48000, true)
  reaper.GetSetProjectInfo(P, "RENDER_CHANNELS", 2, true)
  reaper.GetSetProjectInfo(P, "RENDER_TAILFLAG", 0, true)
  reaper.GetSetProjectInfo_String(P, "RENDER_FILE", OUT, true)
  reaper.GetSetProjectInfo_String(P, "RENDER_PATTERN", name, true)
  reaper.SelectProjectInstance(P)
  reaper.Main_OnCommand(42230, 0)
  -- valores reales de los parámetros (para revisar la normalización de los log)
  local vals = {}
  for _, pv in ipairs(params) do local _, f = reaper.TrackFX_GetFormattedParamValue(tr, fx, pidx(fxk, pv[1]), ""); vals[#vals + 1] = pv[1] .. "=" .. f end
  log("caso", name, table.concat(vals, " "))
end
reaper.SelectProjectInstance(P)
reaper.Main_SaveProject(P, false)
reaper.Main_OnCommand(40860, 0) -- cerrar la pestaña propia
if PREV and PREV ~= P and reaper.ValidatePtr(PREV, "ReaProject*") then reaper.SelectProjectInstance(PREV) end
log("done")
logf:close()
