import httpx

from .base import BaseParser, VideoAuthor, VideoInfo


class PiPiXia(BaseParser):
    """
    皮皮虾
    """

    async def parse_share_url(self, share_url: str) -> VideoInfo:
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.get(share_url, headers=self.get_default_headers())
        location_url = response.headers.get("location", "")
        if len(location_url) <= 0:
            raise Exception("failed to get location url from share url")

        video_id = location_url.split("?")[0].split("/")[-1]

        return await self.parse_video_id(video_id)

    async def parse_video_id(self, video_id: str) -> VideoInfo:
        req_url = f"https://h5.pipix.com/bds/webapi/item/detail/?item_id={video_id}"
        async with httpx.AsyncClient(follow_redirects=False) as client:
            response = await client.get(req_url, headers=self.get_default_headers())
            response.raise_for_status()

        json_data = response.json()
        if json_data["status_code"] != 0:
            raise Exception(f"获取作品信息失败:prompt={json_data['prompt']}")
        data = json_data["data"]["item"]

        author_id = data["author"]["id"]

        # 获取图集图片地址
        images = []
        # 如果data含有 images，并且 images 是一个列表
        if data["note"] is not None:
            for img in data["note"]["multi_image"]:
                images.append(img["url_list"][0]["url"])

        video_url = ""
        if data["video"] is not None:
            video_url = data["video"]["video_download"]["url_list"][0][
                "url"
            ]  # 备用视频地址, 可能有水印
            # comments中可能带有不带水印视频, 但是comments可能为空
            for comment in data.get("comments", []):
                if (
                    comment["item"]["author"]["id"] == author_id
                    and comment["item"]["video"]["video_high"]["url_list"][0]["url"]
                ):
                    video_url = comment["item"]["video"]["video_high"]["url_list"][0][
                        "url"
                    ]
                    break

        video_info = VideoInfo(
            video_url=video_url,
            cover_url=data["cover"]["url_list"][0]["url"],
            title=data["share"]["title"],
            images=images,
            author=VideoAuthor(
                uid=str(author_id),
                name=data["author"]["name"],
                avatar=data["author"]["avatar"]["download_list"][0]["url"],
            ),
        )

        return video_info
