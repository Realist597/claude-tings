--[[
	The amethyst pendant for R6 characters: a chain round the neck and the pendant on the chest.

	Setup (once):
	  1. Import export/Pendant.fbx with the 3D Importer, as one model. It holds:
	       Pendant_Chain    the chain
	       Pendant_Charm    the pendant: its bail, its cage and the stone
	       Ref_Torso        the R6 torso they were fitted to (only used to place them)
	  2. Give Pendant_Chain and Pendant_Charm each a SurfaceAppearance with their four maps from export/
	     (ColorMap, NormalMap, RoughnessMap, MetalnessMap), unless the importer already did.
	  3. Name the model "Pendant" and put it in ServerStorage.
	  4. Put this script in ServerScriptService.

	Every player then spawns wearing it. To hand it out yourself instead, set EQUIP_ON_SPAWN to false and call
	_G.EquipPendant(character) from another server script.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local TEMPLATE = ServerStorage:WaitForChild("Pendant")
local EQUIP_ON_SPAWN = true
local FLIP = false -- set to true if it comes in on the character's back

local PIECES = { "Pendant_Chain", "Pendant_Charm" }

-- where each piece sits on the torso, read once from the template's reference torso
local ref = TEMPLATE:FindFirstChild("Ref_Torso")
assert(ref, "the Pendant model is missing Ref_Torso")
local offsets = {}
for _, name in PIECES do
	local piece = TEMPLATE:FindFirstChild(name)
	assert(piece, "the Pendant model is missing " .. name)
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
	local old = character:FindFirstChild("Pendant")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "Pendant"
	local scale = torso.Size.Y / ref.Size.Y -- 1 on a standard R6 torso
	for _, name in PIECES do
		local piece = TEMPLATE[name]:Clone()
		local offset = offsets[name]
		piece.Size = piece.Size * scale
		piece.Anchored = false
		piece.CanCollide = false
		piece.CanQuery = false
		piece.CanTouch = false
		piece.Massless = true
		piece.CFrame = torso.CFrame * CFrame.new(offset.Position * scale) * offset.Rotation
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = torso
		weld.Part1 = piece
		weld.Parent = piece
		piece.Parent = folder
	end
	folder.Parent = character
end

_G.EquipPendant = equip

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
