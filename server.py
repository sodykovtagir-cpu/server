-- сделано Алексей Н. тг @navalny_12
local encoded_url = "moc.rednerno.zqck-revres//:sptth"

local function get_server_url()
    return string.reverse(encoded_url)
end

local SECRET_TOKEN = "HAsdkrlaaaiwejkdh12AUs"
local last_searched_url = ""

local win = create_window("Naval Браузер", 450, 450)
win:set_bg_color(18, 5, 48, 255) 
win:set_title_color(43, 130, 185, 255)

local url_box = win:add_input(15, 15, 280, 35)
url_box:set_placeholder("url...")

local refresh_btn = win:add_button("R", 305, 15, 40, 35)
refresh_btn:set_color(60, 60, 75, 255)
refresh_btn:set_text_color(255, 255, 255, 255)

-- Тут теперь красуется стрелочка ➤ вместо Go
local go_btn = win:add_button("➤", 355, 15, 80, 35)
go_btn:set_color(43, 130, 185, 255)
go_btn:set_text_color(255, 255, 255, 255)

local page_display = win:add_input(15, 65, 420, 370)
page_display:set_multiline(true)
page_display:set_text("--- Naval Браузер защищён ---\n\nВведи адрес сайта и нажми '➤'.")

local function load_site(target)
    if target == "" then return end
    
    last_searched_url = target
    page_display:set_text("Загрузка через защищённый шлюз...")
    
    local full_url = get_server_url() .. "/browse?url=https://" .. target
    
    local headers = {
        ["X-Auth-Token"] = SECRET_TOKEN
    }
    
    http_get(full_url, function(body, code)
        if code == 200 then
            if body and body ~= "" then
                local clean_text = string.gmatch(body, "[^\r\n]+")
                local lines = {}
                local count = 0
                
                for line in clean_text do
                    if count < 25 then
                        table.insert(lines, line)
                        count = count + 1
                    else
                        break
                    end
                end
                
                page_display:set_text(table.concat(lines, "\n"))
            else
                page_display:set_text("[Ошибка]: Сервер вернул пустой текст.")
            end
        elseif code == 403 then
            page_display:set_text("[Ошибка безопасности]: Сервер отклонён. Неверный токен!")
        else
            page_display:set_text("[Ошибка шлюза]: Код ответа " .. tostring(code))
        end
    end, headers)
end

go_btn:on_click(function()
    local target_url = url_box:get_text()
    target_url = string.gsub(target_url, "https://", "")
    target_url = string.gsub(target_url, "http://", "")
    
    load_site(target_url)
end)

refresh_btn:on_click(function()
    if last_searched_url ~= "" then
        load_site(last_searched_url)
    end
end)
