---
name: trending
track: bonus
kind: live_api
provider: RapidAPI Twitter API45
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [woeid, limit]
outputs: [tool, location, woeid, items]
side_effect: false
---
# trending

Lấy danh sách các trending topics trên Twitter/X tại một địa điểm nhất định.

`woeid` là Yahoo Where On Earth ID:
- 1 = Worldwide (toàn cầu, mặc định)
- 23424840 = Vietnam
- 23424977 = United States
- 44418 = London
- 1132599 = Tokyo

Dùng khi người dùng hỏi "đang trending gì", "hot nhất trên Twitter",
"chủ đề nổi bật hôm nay" mà không chỉ định keyword cụ thể.
