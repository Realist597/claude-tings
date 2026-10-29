--[[
	The Brute for R6 characters: his worn gear, and (optionally) his body and head.

	Setup (once):
	  1. Import export/Brute.fbx with the 3D Importer, as one model. It holds:
	       Brute_Torso, Brute_LeftArm, Brute_RightArm, Brute_LeftLeg, Brute_RightLeg, Brute_Head   the body
	       Brute_Gear_Torso, Brute_Gear_LeftArm, Brute_Gear_RightArm, Brute_Gear_LeftLeg,
	       Brute_Gear_RightLeg                                                                   the gear
	       Brute_Gear_LoinFront, Brute_Gear_LoinBack                       the loincloth's flaps, with bones
	  2. Give each MeshPart a SurfaceAppearance with its maps (see README.md), unless the importer already did.
	  3. Name the model "Brute" and put it in ServerStorage.
	  4. Put this script in ServerScriptService.

	Every player then spawns as the Brute. To hand it out yourself instead, set EQUIP_ON_SPAWN to false and call
	_G.EquipBrute(character) from another server script.

	The gear was fitted to the Brute's own body. On a character with bigger or smaller parts, every piece is
	scaled by how tall that body part is next to the Brute's.
]]

local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local TEMPLATE = ServerStorage:WaitForChild("Brute")
local EQUIP_ON_SPAWN = true
local WEAR_BODY = true -- lay the Brute's body and head over the character's own (hidden) parts
local HIDE_ACCESSORIES = false -- remove hats and hair the character spawns with
local FLIP = false -- set to true if the gear comes in facing backwards

-- each body part's name in the model, and the R6 part it goes on
local PARTS = {
	Torso = "Torso",
	LeftArm = "Left Arm",
	RightArm = "Right Arm",
	LeftLeg = "Left Leg",
	RightLeg = "Right Leg",
	Head = "Head",
}
-- each piece of gear, and the body part it was fitted to and hangs from
local GEAR = {
	Torso = "Torso",
	LeftArm = "LeftArm",
	RightArm = "RightArm",
	LeftLeg = "LeftLeg",
	RightLeg = "RightLeg",
	LoinFront = "Torso",
	LoinBack = "Torso",
}

-- where each piece of gear sits relative to its body part, read once from the template
local offsets = {}
for key, bodyKey in pairs(GEAR) do
	local piece = TEMPLATE:FindFirstChild("Brute_Gear_" .. key)
	local body = TEMPLATE:FindFirstChild("Brute_" .. bodyKey)
	assert(piece and body, "the Brute model is missing Brute_Gear_" .. key .. " or Brute_" .. bodyKey)
	local offset = body.CFrame:ToObjectSpace(piece.CFrame)
	if FLIP then
		offset = CFrame.Angles(0, math.pi, 0) * offset
	end
	offsets[key] = offset
end

-- how much bigger or smaller the character's part is than the Brute's (1 on the Brute's own body)
local function scaleFor(key, bodyPart)
	return bodyPart.Size.Y / TEMPLATE["Brute_" .. key].Size.Y
end

local function attach(piece, bodyPart, cframe, scale, folder)
	piece.Size = piece.Size * scale
	piece.Anchored = false
	piece.CanCollide = false
	piece.CanQuery = false
	piece.CanTouch = false
	piece.Massless = true
	piece.CFrame = cframe
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = bodyPart
	weld.Part1 = piece
	weld.Parent = piece
	piece.Parent = folder
end

local function equip(character)
	local old = character:FindFirstChild("Brute")
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = "Brute"
	if WEAR_BODY then
		for key, partName in pairs(PARTS) do
			local bodyPart = character:WaitForChild(partName, 10)
			if bodyPart then
				local shell = TEMPLATE["Brute_" .. key]:Clone()
				local turn = FLIP and CFrame.Angles(0, math.pi, 0) or CFrame.new()
				attach(shell, bodyPart, bodyPart.CFrame * turn, scaleFor(key, bodyPart), folder)
				bodyPart.Transparency = 1
				for _, item in bodyPart:GetChildren() do
					if item:IsA("Decal") then -- the face moves onto the Brute's head
						item.Parent = shell
					end
				end
			end
		end
	end
	for key, bodyKey in pairs(GEAR) do
		local bodyPart = character:WaitForChild(PARTS[bodyKey], 10)
		if bodyPart then
			local scale = scaleFor(bodyKey, bodyPart)
			local offset = offsets[key]
			local placed = bodyPart.CFrame * CFrame.new(offset.Position * scale) * offset.Rotation
			attach(TEMPLATE["Brute_Gear_" .. key]:Clone(), bodyPart, placed, scale, folder)
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

_G.EquipBrute = equip

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
