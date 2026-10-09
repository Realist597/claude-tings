--[[
	Dark Knight armour for R6 characters.

	Setup (once):
	  1. Import export/ArmorKit.fbx with the 3D Importer. It comes in as a model holding six
	     Armor_* MeshParts and six Ref_* parts (the R6 body the armour was fitted to).
	  2. Give each Armor_* part a SurfaceAppearance with its four maps from export/
	     (ColorMap, NormalMap, RoughnessMap, MetalnessMap), unless the importer already did.
	  3. Name the model "DarkKnightArmor" and put it in ServerStorage.
	  4. Put this script in ServerScriptService.

	Every player then spawns wearing it. To hand it out yourself instead, set EQUIP_ON_SPAWN to
	false and call _G.EquipDarkKnight(character) from another server script.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local TEMPLATE = ServerStorage:WaitForChild("DarkKnightArmor")
local EQUIP_ON_SPAWN = true
local HIDE_ACCESSORIES = true -- hats and hair poke through a closed helm
local FLIP = false -- set to true if the armour comes in facing backwards

local BODY = {
	Head = "Head",
	Torso = "Torso",
	LeftArm = "Left Arm",
	RightArm = "Right Arm",
	LeftLeg = "Left Leg",
	RightLeg = "Right Leg",
}

-- where each piece sits relative to its body part, read once from the template's reference body
local offsets = {}
for key in pairs(BODY) do
	local armor = TEMPLATE:FindFirstChild("Armor_" .. key)
	local ref = TEMPLATE:FindFirstChild("Ref_" .. key)
	assert(armor and ref, "DarkKnightArmor is missing Armor_" .. key .. " or Ref_" .. key)
	local offset = ref.CFrame:ToObjectSpace(armor.CFrame)
	if FLIP then
		offset = CFrame.Angles(0, math.pi, 0) * offset
	end
	offsets[key] = offset
end

local function equip(character)
	local old = character:FindFirstChild("DarkKnightArmor")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "DarkKnightArmor"
	for key, partName in pairs(BODY) do
		local bodyPart = character:WaitForChild(partName, 10)
		if bodyPart then
			local piece = TEMPLATE["Armor_" .. key]:Clone()
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

_G.EquipDarkKnight = equip

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
