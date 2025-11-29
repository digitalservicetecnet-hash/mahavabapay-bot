-- Redis LUA script for atomic balance updates
-- This ensures race-condition-free balance operations

local key = KEYS[1]
local delta = tonumber(ARGV[1])
local balance = tonumber(redis.call("GET", key) or "0")

local newbal = balance + delta

-- Prevent negative balance
if newbal < 0 then
    return {err="insufficient_funds"}
end

redis.call("SET", key, newbal)
return newbal
