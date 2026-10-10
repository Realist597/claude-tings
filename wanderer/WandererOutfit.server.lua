--[[
	The Wanderer outfit for R6 characters.

	Setup (once):
	  1. Import export/WandererOutfit.fbx with the 3D Importer. It comes in as a model holding eight
	     Wanderer_* MeshParts (the hat, the torso, both arms and both legs, plus the cape and the
	     scarf, which have bones) and six Ref_* parts (the R6 body the outfit was fitted to).
	  2. Give each Wanderer_* part a SurfaceAppearance with its four maps from export/
	     (ColorMap, NormalMap, RoughnessMap, MetalnessMap), unless the importer already did.
	  3. Name the model "WandererOutfit" and put it in ServerStorage.
	  4. Put this script in ServerScriptService.

	Every player then spawns wearing it. To hand it out yourself instead, set EQUIP_ON_SPAWN to
	false and call _G.EquipWanderer(character) from another server script.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local TEMPLATE = ServerStorage:WaitForChild("WandererOutfit")
local EQUIP_ON_SPAWN = true
local HIDE_ACCESSORIES = true -- other hats and hair would poke through the cowboy hat
local FLIP = false -- set to true if the outfit comes in facing backwards

local BODY = {
	Hat = "Head",
	Torso = "Torso",
	LeftArm = "Left Arm",
	RightArm = "Right Arm",
	LeftLeg = "Left Leg",
	RightLeg = "Right Leg",
	Cape = "Torso",
	Scarf = "Torso",
}
-- the reference body part each piece was fitted against (the hat sits on the head, the cloth hangs off the torso)
local REF = { Hat = "Head", Cape = "Torso", Scarf = "Torso" }

-- where each piece sits relative to its body part, read once from the template's reference body
local offsets = {}
for key in pairs(BODY) do
	local piece = TEMPLATE:FindFirstChild("Wanderer_" .. key)
	local refKey = REF[key] or key
	local ref = TEMPLATE:FindFirstChild("Ref_" .. refKey)
	assert(piece and ref, "WandererOutfit is missing Wanderer_" .. key .. " or Ref_" .. refKey)
	local offset = ref.CFrame:ToObjectSpace(piece.CFrame)
	if FLIP then
		offset = CFrame.Angles(0, math.pi, 0) * offset
	end
	offsets[key] = offset
end

local function equip(character)
	local old = character:FindFirstChild("WandererOutfit")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "WandererOutfit"
	for key, partName in pairs(BODY) do
		local bodyPart = character:WaitForChild(partName, 10)
		if bodyPart then
			local piece = TEMPLATE["Wanderer_" .. key]:Clone()
			piece.Anchored = false
			piece.CanCollide = false
			piece.CanQuery = false
			piece.CanTouch = false
			piece.Massless = true
			piece.CFrame = bodyPart.CFrame * offsets[key]
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = bodyPart
			weld.Part1 = piece
			weld.Parent = piece
			piece.Parent = folder
		end
	end
	folder.Parent = character
	if HIDE_ACCESSORIES then
		for _, item in character:GetChildren() do
			if item:IsA("Accessory") then
				item:Destroy()
			end
		end
	end
end

_G.EquipWanderer = equip

if EQUIP_ON_SPAWN then
	local function onPlayer(player)
		player.CharacterAppearanceLoaded:Connect(equip)
		if player.Character and player:HasAppearanceLoaded() then
			equip(player.Character)
		end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
end
