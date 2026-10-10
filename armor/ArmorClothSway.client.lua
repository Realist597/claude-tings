--[[
	Moves the Dark Knight's cloth: the cape streams back as you run and lifts when you fall, with a
	slow sway when standing still; the front panel flaps forward as the legs swing.

	Roblox has no cloth physics, so this turns the bones in Armor_Cape and Armor_Tabard every frame.
	Put it in StarterPlayer > StarterPlayerScripts as a LocalScript. It animates every player's armour
	(bone motion is drawn on each player's own screen, so every client runs it).

	If a cloth swings into the body instead of away from it, flip CAPE_SIGN or TABARD_SIGN.
]]

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local CAPE_SIGN = 1
local TABARD_SIGN = -1
local CAPE_RUN = math.rad(14) -- per bone (4 down the cape) at a full run
local CAPE_FALL = math.rad(10) -- per bone, extra lift when falling fast
local CAPE_IDLE = math.rad(1.2) -- per bone, the slow sway when standing
local TABARD_SWING = math.rad(12) -- per bone (3 down the panel) at a full stride
local RUN_SPEED = 16 -- studs/s that counts as a full run
local STIFFNESS = 6 -- how quickly the cloth catches up (higher = snappier)

-- bones of a cloth part, grouped by chain and ordered top to bottom
local function chains(part, prefix)
	local out = {}
	for _, bone in part:GetDescendants() do
		if bone:IsA("Bone") then
			local c, r = bone.Name:match("^" .. prefix .. "_(%d+)_(%d+)$")
			if not c then
				r = bone.Name:match("^" .. prefix .. "_(%d+)$")
				c = r and "0"
			end
			if c then
				c, r = tonumber(c), tonumber(r)
				out[c + 1] = out[c + 1] or {}
				out[c + 1][r + 1] = bone
			end
		end
	end
	return out
end

local states = {} -- [armour folder] = { torso, cape, tabard, capeAngle, tabardAngle, phase }

local function stateFor(folder)
	local s = states[folder]
	if s then
		return s
	end
	local character = folder.Parent
	local torso = character and character:FindFirstChild("Torso")
	if not torso then
		return nil
	end
	local cape = folder:FindFirstChild("Armor_Cape")
	local tabard = folder:FindFirstChild("Armor_Tabard")
	s = {
		torso = torso,
		cape = cape and chains(cape, "Cape") or {},
		tabard = tabard and chains(tabard, "Tabard") or {},
		capeAngle = 0,
		tabardAngle = 0,
		phase = math.random() * 10,
	}
	states[folder] = s
	folder.AncestryChanged:Connect(function(_, parent)
		if not parent then
			states[folder] = nil
		end
	end)
	return s
end

-- turn a bone about the torso's left-right axis (whatever way the bone itself is oriented)
local function swing(bone, torso, angle)
	local axis = bone.WorldCFrame:VectorToObjectSpace(torso.CFrame.RightVector)
	bone.Transform = CFrame.fromAxisAngle(axis, angle)
end

RunService.RenderStepped:Connect(function(dt)
	local t = os.clock()
	local catch = math.min(1, dt * STIFFNESS)
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local folder = character and character:FindFirstChild("DarkKnightArmor")
		local s = folder and stateFor(folder)
		if s then
			local torso = s.torso
			local v = torso.CFrame:VectorToObjectSpace(torso.AssemblyLinearVelocity)
			local forward = math.max(0, -v.Z) -- the torso faces -Z
			local falling = math.max(0, -v.Y)

			local capeTarget = math.clamp(forward / RUN_SPEED, 0, 1.3) * CAPE_RUN
				+ math.clamp(falling / 50, 0, 1) * CAPE_FALL
			s.capeAngle += (capeTarget - s.capeAngle) * catch
			local flutter = 1 + math.clamp(forward / RUN_SPEED, 0, 1) * 1.5
			for c, chain in s.cape do
				for r, bone in chain do
					local wave = math.sin(t * 1.8 + s.phase + r * 0.9 + c * 0.7) * CAPE_IDLE * flutter
					swing(bone, torso, CAPE_SIGN * (s.capeAngle * (0.7 + 0.2 * r) + wave))
				end
			end

			local stride = 0
			for _, hipName in { "Left Hip", "Right Hip" } do
				local hip = torso:FindFirstChild(hipName)
				if hip and hip:IsA("Motor6D") then
					stride = math.max(stride, math.abs(hip.CurrentAngle))
				end
			end
			local tabardTarget = math.clamp(stride, 0, 1) * TABARD_SWING
			s.tabardAngle += (tabardTarget - s.tabardAngle) * catch
			for _, chain in s.tabard do
				for r, bone in chain do
					swing(bone, torso, TABARD_SIGN * s.tabardAngle * (0.8 + 0.2 * r))
				end
			end
		end
	end
end)
