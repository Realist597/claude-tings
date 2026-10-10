--[[
	Quiver for R6 characters.

	Setup (once):
	  1. Import export/QuiverKit.fbx with the 3D Importer. It comes in as a model holding the Quiver and
	     Quiver_Arrows MeshParts, and Ref_Torso (the R6 torso they were fitted to).
	  2. Give Quiver a SurfaceAppearance with export/Quiver_Color, _Normal, _Roughness and _Metalness, and
	     Quiver_Arrows one with the Quiver_Arrows_* maps. For the glow, use the _Emissive map as the emissive
	     mask and raise EmissiveStrength.
	  3. Name the model "QuiverKit" and put it in ServerStorage.
	  4. Put this script in ServerScriptService.

	Every player then spawns wearing it. To hand it out yourself instead, set EQUIP_ON_SPAWN to false and
	call _G.EquipQuiver(character) from another server script.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local TEMPLATE = ServerStorage:WaitForChild("QuiverKit")
local EQUIP_ON_SPAWN = true
local FLIP = false -- set to true if the quiver comes in on the chest instead of the back

local PIECES = { "Quiver", "Quiver_Arrows" }
local ref = TEMPLATE:WaitForChild("Ref_Torso")
local offsets = {}
for _, name in PIECES do
	local piece = TEMPLATE:WaitForChild(name)
	local offset = ref.CFrame:ToObjectSpace(piece.CFrame)
	if FLIP then
		offset = CFrame.Angles(0, math.pi, 0) * offset
	end
	offsets[name] = offset
end

local function equip(character)
	local torso = character:WaitForChild("Torso", 10)
	if not torso then
		return
	end
	local old = character:FindFirstChild("QuiverKit")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "QuiverKit"
	for _, name in PIECES do
		local piece = TEMPLATE[name]:Clone()
		piece.Anchored = false
		piece.CanCollide = false
		piece.CanQuery = false
		piece.CanTouch = false
		piece.Massless = true
		piece.CFrame = torso.CFrame * offsets[name]
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = torso
		weld.Part1 = piece
		weld.Parent = piece
		piece.Parent = folder
	end
	folder.Parent = character
end

_G.EquipQuiver = equip

if EQUIP_ON_SPAWN then
	local function onPlayer(player)
		player.CharacterAdded:Connect(equip)
		if player.Character then
			equip(player.Character)
		end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
end
