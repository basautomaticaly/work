import requests,re,threading,os, sys,random,copy,random,json,httpx,hashlib
from loguru import logger
from wmi import WMI  
from urllib.request import urlopen
from time import sleep
from colorama import init, Fore, Style
from urllib.parse import urlencode
from typing import Union, List

__version__ = "2-5"

HWID = WMI().Win32_ComputerSystemProduct()[0].UUID

CLIENTS = {
    "MWEB": {
        'context': {
            'client': {
                'clientName': 'MWEB',
                'clientVersion': '2.20211109.01.00'
            }
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    "ANDROID": {
        'context': {
            'client': {
                'clientName': 'ANDROID',
                'clientVersion': '16.20'
            }
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    "ANDROID_EMBED": {
        'context': {
            'client': {
                'clientName': 'ANDROID',
                'clientVersion': '16.20',
                'clientScreen': 'EMBED'
            }
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    },
    "TV_EMBED": {
        "context": {
            "client": {
                "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
                "clientVersion": "2.0"
            },
            "thirdParty": {
                "embedUrl": "https://www.youtube.com/",
            }
        },
        'api_key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
    }
}

requestPayload = {
    "context": {
        "client": {
            "clientName": "WEB",
            "clientVersion": "2.20210224.06.00",
            "newVisitorCookie": True,
        },
        "user": {
            "lockedSafetyMode": False,
        }
    }
}
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
searchKey = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'

videoElementKey = 'videoRenderer'
channelElementKey = 'channelRenderer'
playlistElementKey = 'playlistRenderer'
shelfElementKey = 'shelfRenderer'
itemSectionKey = 'itemSectionRenderer'
continuationItemKey = 'continuationItemRenderer'
richItemKey = 'richItemRenderer'
hashtagVideosPath = ['contents', 'twoColumnBrowseResultsRenderer', 'tabs', 0, 'tabRenderer', 'content', 'richGridRenderer', 'contents']
hashtagContinuationVideosPath = ['onResponseReceivedActions', 0, 'appendContinuationItemsAction', 'continuationItems']
contentPath = ['contents', 'twoColumnSearchResultsRenderer', 'primaryContents', 'sectionListRenderer', 'contents']
fallbackContentPath = ['contents', 'twoColumnSearchResultsRenderer', 'primaryContents', 'richGridRenderer', 'contents']
continuationContentPath = ['onResponseReceivedCommands', 0, 'appendContinuationItemsAction', 'continuationItems']
continuationKeyPath = ['continuationItemRenderer', 'continuationEndpoint', 'continuationCommand', 'token']




def getValue(source: dict, path: List[str]) -> Union[str, int, dict, None]:
    value = source
    for key in path:
        if type(key) is str:
            if key in value.keys():
                value = value[key]
            else:
                value = None
                break
        elif type(key) is int:
            if len(value) != 0:
                value = value[key]
            else:
                value = None
                break
    return value


def getVideoId(videoLink: str) -> str:
    if 'youtu.be' in videoLink:
        if videoLink[-1] == '/':
            return videoLink.split('/')[-2]
        return videoLink.split('/')[-1]
    elif 'youtube.com' in videoLink:
        if '&' not in videoLink:
            return videoLink[videoLink.index('v=') + 2:]
        return videoLink[videoLink.index('v=') + 2: videoLink.index('&')]
    else:
        return videoLink

class ComponentHandler:
    def _getVideoComponent(self, element: dict, shelfTitle: str = None) -> dict:
        video = element[videoElementKey]
        component = {
            'type':                           'video',
            'id':                              self._getValue(video, ['videoId']),
            'title':                           self._getValue(video, ['title', 'runs', 0, 'text']),
            'publishedTime':                   self._getValue(video, ['publishedTimeText', 'simpleText']),
            'duration':                        self._getValue(video, ['lengthText', 'simpleText']),
            'viewCount': {
                'text':                        self._getValue(video, ['viewCountText', 'simpleText']),
                'short':                       self._getValue(video, ['shortViewCountText', 'simpleText']),
            },
            'thumbnails':                      self._getValue(video, ['thumbnail', 'thumbnails']),
            'richThumbnail':                   self._getValue(video, ['richThumbnail', 'movingThumbnailRenderer', 'movingThumbnailDetails', 'thumbnails', 0]),
            'descriptionSnippet':              self._getValue(video, ['detailedMetadataSnippets', 0, 'snippetText', 'runs']),
            'channel': {
                'name':                        self._getValue(video, ['ownerText', 'runs', 0, 'text']),
                'id':                          self._getValue(video, ['ownerText', 'runs', 0, 'navigationEndpoint', 'browseEndpoint', 'browseId']),
                'thumbnails':                  self._getValue(video, ['channelThumbnailSupportedRenderers', 'channelThumbnailWithLinkRenderer', 'thumbnail', 'thumbnails']),
            },
            'accessibility': {
                'title':                       self._getValue(video, ['title', 'accessibility', 'accessibilityData', 'label']),
                'duration':                    self._getValue(video, ['lengthText', 'accessibility', 'accessibilityData', 'label']),
            },
        }
        component['link'] = 'https://www.youtube.com/watch?v=' + component['id']
        component['channel']['link'] = 'https://www.youtube.com/channel/' + component['channel']['id']
        component['shelfTitle'] = shelfTitle
        return component

    def _getChannelComponent(self, element: dict) -> dict:
        channel = element[channelElementKey]
        component = {
            'type':                           'channel',
            'id':                              self._getValue(channel, ['channelId']),
            'title':                           self._getValue(channel, ['title', 'simpleText']),
            'thumbnails':                      self._getValue(channel, ['thumbnail', 'thumbnails']),
            'videoCount':                      self._getValue(channel, ['videoCountText', 'runs', 0, 'text']),
            'descriptionSnippet':              self._getValue(channel, ['descriptionSnippet', 'runs']),
            'subscribers':                     self._getValue(channel, ['subscriberCountText', 'simpleText']),
        }
        component['link'] = 'https://www.youtube.com/channel/' + component['id']
        return component

    
    
    def _getVideoFromChannelSearch(self, elements: list) -> list:
        channelsearch = []
        for element in elements:
            element = self._getValue(element, ["childVideoRenderer"])
            json = {
                "id":                                    self._getValue(element, ["videoId"]),
                "title":                                 self._getValue(element, ["title", "simpleText"]),
                "uri":                                   self._getValue(element, ["navigationEndpoint", "commandMetadata", "webCommandMetadata", "url"]),
                "duration": {
                    "simpleText":                        self._getValue(element, ["lengthText", "simpleText"]),
                    "text":                              self._getValue(element, ["lengthText", "accessibility", "accessibilityData", "label"])
                }
            }
            channelsearch.append(json)
        return channelsearch
    
    def _getChannelSearchComponent(self, elements: list) -> list:
        channelsearch = []
        for element in elements:
            responsetype = None

            if 'gridPlaylistRenderer' in element:
                element = element['gridPlaylistRenderer']
                responsetype = 'gridplaylist'
            elif 'itemSectionRenderer' in element:
                first_content = element["itemSectionRenderer"]["contents"][0]
                if 'videoRenderer' in first_content:
                    element = first_content['videoRenderer']
                    responsetype = "video"
                elif 'playlistRenderer' in first_content:
                    element = first_content["playlistRenderer"]
                    responsetype = "playlist"
                else:
                    raise Exception(f'Unexpected first_content {first_content}')
            elif 'continuationItemRenderer' in element:
                # for endless scrolling, not needed here
                # TODO: Implement endless scrolling
                continue
            else:
                raise Exception(f'Unexpected element {element}')
            
            if responsetype == "video":
                json = {
                    "id":                                    self._getValue(element, ["videoId"]),
                    "thumbnails": {
                        "normal":                            self._getValue(element, ["thumbnail", "thumbnails"]),
                        "rich":                              self._getValue(element, ["richThumbnail", "movingThumbnailRenderer", "movingThumbnailDetails", "thumbnails"])
                    },
                    "title":                                 self._getValue(element, ["title", "runs", 0, "text"]),
                    "descriptionSnippet":                    self._getValue(element, ["descriptionSnippet", "runs", 0, "text"]),
                    "uri":                                   self._getValue(element, ["navigationEndpoint", "commandMetadata", "webCommandMetadata", "url"]),
                    "views": {
                        "precise":                           self._getValue(element, ["viewCountText", "simpleText"]),
                        "simple":                            self._getValue(element, ["shortViewCountText", "simpleText"]),
                        "approximate":                       self._getValue(element, ["shortViewCountText", "accessibility", "accessibilityData", "label"])
                    },
                    "duration": {
                        "simpleText":                        self._getValue(element, ["lengthText", "simpleText"]),
                        "text":                              self._getValue(element, ["lengthText", "accessibility", "accessibilityData", "label"])
                    },
                    "published":                             self._getValue(element, ["publishedTimeText", "simpleText"]),
                    "channel": {
                        "name":                              self._getValue(element, ["ownerText", "runs", 0, "text"]),
                        "thumbnails":                        self._getValue(element, ["channelThumbnailSupportedRenderers", "channelThumbnailWithLinkRenderer", "thumbnail", "thumbnails"])
                    },
                    "type":                                  responsetype
                }
            elif responsetype == 'playlist':
                json = {
                    "id":                                    self._getValue(element, ["playlistId"]),
                    "videos":                                self._getVideoFromChannelSearch(self._getValue(element, ["videos"])),
                    "thumbnails": {
                        "normal":                            self._getValue(element, ["thumbnails"]),
                    },
                    "title":                                 self._getValue(element, ["title", "simpleText"]),
                    "uri":                                   self._getValue(element, ["navigationEndpoint", "commandMetadata", "webCommandMetadata", "url"]),
                    "channel": {
                        "name":                              self._getValue(element, ["longBylineText", "runs", 0, "text"]),
                    },
                    "type":                                  responsetype
                }
            else:
                json = {
                    "id":                                    self._getValue(element, ["playlistId"]),
                    "thumbnails": {
                        "normal":                            self._getValue(element, ["thumbnail", "thumbnails", 0]),
                    },
                    "title":                                 self._getValue(element, ["title", "runs", 0, "text"]),
                    "uri":                                   self._getValue(element, ["navigationEndpoint", "commandMetadata", "webCommandMetadata", "url"]),
                    "type":                                  'playlist'
                }
            channelsearch.append(json)
        return channelsearch

    def _getShelfComponent(self, element: dict) -> dict:
        shelf = element[shelfElementKey]
        return {
            'title':                           self._getValue(shelf, ['title', 'simpleText']),
            'elements':                        self._getValue(shelf, ['content', 'verticalListRenderer', 'items']),
        }

    def _getValue(self, source: dict, path: List[str]) -> Union[str, int, dict, None]:
        value = source
        for key in path:
            if type(key) is str:
                if key in value.keys():
                    value = value[key]
                else:
                    value = None
                    break
            elif type(key) is int:
                if len(value) != 0:
                    value = value[key]
                else:
                    value = None
                    break
        return value

class RequestHandler(ComponentHandler):
    def _makeRequest(self) -> None:
        ''' Fixes #47 '''
        requestBody = copy.deepcopy(requestPayload)
        requestBody['query'] = self.query
        requestBody['client'] = {
            'hl': self.language,
            'gl': self.region,
        }
        if self.searchPreferences:
            requestBody['params'] = self.searchPreferences
        if self.continuationKey:
            requestBody['continuation'] = self.continuationKey
        requestBodyBytes = json.dumps(requestBody).encode('utf_8')
        request = Request(
            'https://www.youtube.com/youtubei/v1/search' + '?' + urlencode({
                'key': searchKey,
            }),
            data = requestBodyBytes,
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Content-Length': len(requestBodyBytes),
                'User-Agent': userAgent,
            }
        )
        try:
            self.response = urlopen(request, timeout=self.timeout).read().decode('utf_8')
        except (Exception,):
            return self._makeRequest()
    
    def _parseSource(self) -> None:
        try:
            if not self.continuationKey:
                responseContent = self._getValue(json.loads(self.response), contentPath)
            else:
                responseContent = self._getValue(json.loads(self.response), continuationContentPath)
            if responseContent:
                for element in responseContent:
                    if itemSectionKey in element.keys():
                        self.responseSource = self._getValue(element, [itemSectionKey, 'contents'])
                    if continuationItemKey in element.keys():
                        self.continuationKey = self._getValue(element, continuationKeyPath)
            else:
                self.responseSource = self._getValue(json.loads(self.response), fallbackContentPath)
                self.continuationKey = self._getValue(self.responseSource[-1], continuationKeyPath)
        except:
            raise Exception('ERROR: Could not parse YouTube response.')




class RequestCore:
    def __init__(self):
        self.url = None
        self.data = None
        self.timeout = 2
        self.proxy = []
        proxy = open("proxy.txt", "r").read().splitlines()
        for p in proxy:
            p_split = p.split(':')
            if len(p_split) == 2:#ip:port
                self.proxy.append({"http://": "http://"+p})
            elif len(p_split) == 4:#ip:port:login:password
                self.proxy.append({"http://": f"http://{p_split[2]}:{p_split[3]}@{p_split[0]}:{p_split[1]}"})
            elif '@' in p:#login:password@ip:port
                self.proxy.append({"http://": "http://"+p})
            
            

    def syncPostRequest(self) -> httpx.Response:
        try:
            r = httpx.post(
                self.url,
                headers={"User-Agent": userAgent},
                json=self.data,
                timeout=self.timeout,
                proxies=random.choice(self.proxy)
            )
            if r.status_code == 200:
                return r
            else:
                return self.syncPostRequest()
        except (Exception,):
            return self.syncPostRequest()

    async def asyncPostRequest(self) -> httpx.Response:
        try:
            async with httpx.AsyncClient(proxies=random.choice(self.proxy)) as client:
                r = await client.post(self.url, headers={"User-Agent": userAgent}, json=self.data, timeout=self.timeout)
                if r.status_code == 200:
                    return r
                else:
                    return self.asyncPostRequest()
        except (Exception,):
            return await self.asyncPostRequest()

    def syncGetRequest(self) -> httpx.Response:
        try:
            r = httpx.get(self.url, headers={"User-Agent": userAgent}, timeout=self.timeout,
                             cookies={'CONSENT': 'YES+1'}, proxies=random.choice(self.proxy))
            if r.status_code == 200:
                return r
            else:
                return self.syncGetRequest()
        except (Exception,):
            return self.syncGetRequest()

    async def asyncGetRequest(self) -> httpx.Response:
        try:
            async with httpx.AsyncClient(proxies=random.choice(self.proxy)) as client:
                r = await client.get(self.url, headers={"User-Agent": userAgent}, timeout=self.timeout,
                                     cookies={'CONSENT': 'YES+1'})
                if r.status_code == 200:
                    return r
                else:
                    return await self.asyncGetRequest()
        except (Exception,):
            return await self.asyncGetRequest()




class VideoCore(RequestCore):
    def __init__(self, videoLink: str, componentMode: str, resultMode: int, timeout: int, enableHTML: bool, overridedClient: str = "ANDROID"):
        super().__init__()
        self.timeout = timeout
        self.resultMode = resultMode
        self.componentMode = componentMode
        self.videoLink = videoLink
        self.enableHTML = enableHTML
        self.overridedClient = overridedClient
    
    # We call this when we use only HTML
    def post_request_only_html_processing(self):
        self.__getVideoComponent(self.componentMode)
        self.result = self.__videoComponent

    def post_request_processing(self):
        self.__parseSource()
        self.__getVideoComponent(self.componentMode)
        self.result = self.__videoComponent

    def prepare_innertube_request(self):
        self.url = 'https://www.youtube.com/youtubei/v1/player' + "?" + urlencode({
            'key': searchKey,
            'contentCheckOk': True,
            'racyCheckOk': True,
            "videoId": getVideoId(self.videoLink)
        })
        self.data = copy.deepcopy(CLIENTS[self.overridedClient])

    async def async_create(self):
        self.prepare_innertube_request()
        response = await self.asyncPostRequest()
        self.response = response.text
        if response.status_code == 200:
            self.post_request_processing()
        else:
            raise Exception('ERROR: Invalid status code.')

    def sync_create(self):
        self.prepare_innertube_request()
        response = self.syncPostRequest()
        self.response = response.text
        if response.status_code == 200:
            self.post_request_processing()
        else:
            raise Exception('ERROR: Invalid status code.')

    def prepare_html_request(self):
        self.url = 'https://www.youtube.com/youtubei/v1/player' + "?" + urlencode({
            'key': searchKey,
            'contentCheckOk': True,
            'racyCheckOk': True,
            "videoId": getVideoId(self.videoLink)
        })
        self.data = CLIENTS["MWEB"]

    def sync_html_create(self):
        self.prepare_html_request()
        response = self.syncPostRequest()
        self.HTMLresponseSource = response.json()

    async def async_html_create(self):
        self.prepare_html_request()
        response = await self.asyncPostRequest()
        self.HTMLresponseSource = response.json()

    def __parseSource(self) -> None:
        try:
            self.responseSource = json.loads(self.response)
        except Exception as e:
            raise Exception('ERROR: Could not parse YouTube response.')

    def __result(self, mode: int) -> Union[dict, str]:
        if mode == ResultMode.dict:
            return self.__videoComponent
        elif mode == ResultMode.json:
            return json.dumps(self.__videoComponent, indent=4)

    def __getVideoComponent(self, mode: str) -> None:
        videoComponent = {}
        if mode in ['getInfo', None]:
            try:
                responseSource = self.responseSource
            except:
                responseSource = None
            if self.enableHTML:
                responseSource = self.HTMLresponseSource
            component = {
                'id': getValue(responseSource, ['videoDetails', 'videoId']),
                'title': getValue(responseSource, ['videoDetails', 'title']),
                'duration': {
                    'secondsText': getValue(responseSource, ['videoDetails', 'lengthSeconds']),
                },
                'viewCount': {
                    'text': getValue(responseSource, ['videoDetails', 'viewCount'])
                },
                'thumbnails': getValue(responseSource, ['videoDetails', 'thumbnail', 'thumbnails']),
                'description': getValue(responseSource, ['videoDetails', 'shortDescription']),
                'channel': {
                    'name': getValue(responseSource, ['videoDetails', 'author']),
                    'id': getValue(responseSource, ['videoDetails', 'channelId']),
                },
                'allowRatings': getValue(responseSource, ['videoDetails', 'allowRatings']),
                'averageRating': getValue(responseSource, ['videoDetails', 'averageRating']),
                'keywords': getValue(responseSource, ['videoDetails', 'keywords']),
                'isLiveContent': getValue(responseSource, ['videoDetails', 'isLiveContent']),
                'publishDate': getValue(responseSource, ['microformat', 'playerMicroformatRenderer', 'publishDate']),
                'uploadDate': getValue(responseSource, ['microformat', 'playerMicroformatRenderer', 'uploadDate']),
                'isFamilySafe': getValue(responseSource, ['microformat', 'playerMicroformatRenderer', 'isFamilySafe']),
                'category': getValue(responseSource, ['microformat', 'playerMicroformatRenderer', 'category']),
            }
            component['isLiveNow'] = component['isLiveContent'] and component['duration']['secondsText'] == "0"
            component['link'] = 'https://www.youtube.com/watch?v=' + component['id']
            component['channel']['link'] = 'https://www.youtube.com/channel/' + component['channel']['id']
            videoComponent.update(component)
        if mode in ['getFormats', None]:
            videoComponent.update(
                {
                    "streamingData": getValue(self.responseSource, ["streamingData"])
                }
            )
        if self.enableHTML:
            videoComponent["publishDate"] = getValue(self.HTMLresponseSource, ['microformat', 'playerMicroformatRenderer', 'publishDate'])
            videoComponent["uploadDate"] = getValue(self.HTMLresponseSource, ['microformat', 'playerMicroformatRenderer', 'uploadDate'])
        self.__videoComponent = videoComponent




class ResultMode:
    json = 0
    dict = 1


class SearchMode:
    videos = 'EgIQAQ%3D%3D'
    channels = 'EgIQAg%3D%3D'
    playlists = 'EgIQAw%3D%3D'
    livestreams = 'EgJAAQ%3D%3D'




class Video:
    @staticmethod
    def get(videoLink: str, mode: int = ResultMode.dict, timeout: int = None, get_upload_date: bool = False) -> Union[
        dict, str, None]:
        vc = VideoCore(videoLink, None, mode, timeout, get_upload_date)
        if get_upload_date:
            vc.sync_html_create()
        vc.sync_create()
        return vc.result


class ChannelSearchCore(RequestCore, ComponentHandler):
    response = None
    responseSource = None
    resultComponents = []

    def __init__(self, query: str, language: str, region: str, searchPreferences: str, browseId: str, timeout: int):
        super().__init__()
        self.query = query
        self.language = language
        self.region = region
        self.browseId = browseId
        self.searchPreferences = searchPreferences
        self.continuationKey = None
        self.timeout = timeout

    def sync_create(self):
        self._syncRequest()
        self._parseChannelSearchSource()
        self.response = self._getChannelSearchComponent(self.response)

    async def next(self):
        await self._asyncRequest()
        self._parseChannelSearchSource()
        self.response = self._getChannelSearchComponent(self.response)
        return self.response

    def _parseChannelSearchSource(self) -> None:
        try:
            last_tab = self.response["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][-1]
            if 'expandableTabRenderer' in last_tab:
                self.response = last_tab["expandableTabRenderer"]["content"]["sectionListRenderer"]["contents"]
            else:
                tab_renderer = last_tab["tabRenderer"]
                if 'content' in tab_renderer:
                    self.response = tab_renderer["content"]["sectionListRenderer"]["contents"]
                else:
                    self.response = []
        except:
            raise Exception('ERROR: Could not parse YouTube response.')

    def _getRequestBody(self):
        ''' Fixes #47 '''
        requestBody = copy.deepcopy(requestPayload)
        requestBody['query'] = self.query
        requestBody['client'] = {
            'hl': self.language,
            'gl': self.region,
        }
        requestBody['params'] = self.searchPreferences
        requestBody['browseId'] = self.browseId
        self.url = 'https://www.youtube.com/youtubei/v1/browse' + '?' + urlencode({
            'key': searchKey,
        })
        self.data = requestBody

    def _syncRequest(self) -> None:
        ''' Fixes #47 '''
        self._getRequestBody()

        request = self.syncPostRequest()
        try:
            self.response = request.json()
        except:
            raise Exception('ERROR: Could not make request.')

    async def _asyncRequest(self) -> None:
        ''' Fixes #47 '''
        self._getRequestBody()

        request = await self.asyncPostRequest()
        try:
            self.response = request.json()
        except:
            raise Exception('ERROR: Could not make request.')

    def result(self, mode: int = ResultMode.dict) -> Union[str, dict]:
        '''Returns the search result.
        Args:
            mode (int, optional): Sets the type of result. Defaults to ResultMode.dict.
        Returns:
            Union[str, dict]: Returns JSON or dictionary.
        '''
        if mode == ResultMode.json:
            return json.dumps({'result': self.response}, indent=4)
        elif mode == ResultMode.dict:
            return {'result': self.response}



class SearchCore(RequestCore, RequestHandler, ComponentHandler):
    response = None
    responseSource = None
    resultComponents = []

    def __init__(self, query: str, limit: int, language: str, region: str, searchPreferences: str, timeout: int):
        super().__init__()
        self.query = query
        self.limit = limit
        self.language = language
        self.region = region
        self.searchPreferences = searchPreferences
        self.timeout = timeout
        self.continuationKey = None

    def sync_create(self):
        self._makeRequest()
        self._parseSource()

    def _getRequestBody(self):
        ''' Fixes #47 '''
        requestBody = copy.deepcopy(requestPayload)
        requestBody['query'] = self.query
        requestBody['client'] = {
            'hl': self.language,
            'gl': self.region,
        }
        if self.searchPreferences:
            requestBody['params'] = self.searchPreferences
        if self.continuationKey:
            requestBody['continuation'] = self.continuationKey
        self.url = 'https://www.youtube.com/youtubei/v1/search' + '?' + urlencode({
            'key': searchKey,
        })
        self.data = requestBody

    def _makeRequest(self) -> None:
        self._getRequestBody()
        request = self.syncPostRequest()
        try:
            self.response = request.text
        except:
            raise Exception('ERROR: Could not make request.')

    async def _makeAsyncRequest(self) -> None:
        self._getRequestBody()
        request = await self.asyncPostRequest()
        try:
            self.response = request.text
        except:
            raise Exception('ERROR: Could not make request.')

    def result(self, mode: int = ResultMode.dict) -> Union[str, dict]:
        if mode == ResultMode.json:
            return json.dumps({'result': self.resultComponents}, indent=4)
        elif mode == ResultMode.dict:
            return {'result': self.resultComponents}

    def _next(self) -> bool:
        if self.continuationKey:
            self.response = None
            self.responseSource = None
            self.resultComponents = []
            self._makeRequest()
            self._parseSource()
            self._getComponents(*self.searchMode)
            return True
        else:
            return False

    async def _nextAsync(self) -> dict:
        self.response = None
        self.responseSource = None
        self.resultComponents = []
        await self._makeAsyncRequest()
        self._parseSource()
        self._getComponents(*self.searchMode)
        return {
            'result': self.resultComponents,
        }

    def _getComponents(self, findVideos: bool, findChannels: bool, findPlaylists: bool) -> None:
        self.resultComponents = []
        for element in self.responseSource:
            if videoElementKey in element.keys() and findVideos:
                self.resultComponents.append(self._getVideoComponent(element))
            if channelElementKey in element.keys() and findChannels:
                self.resultComponents.append(self._getChannelComponent(element))
            if shelfElementKey in element.keys() and findVideos:
                for shelfElement in self._getShelfComponent(element)['elements']:
                    self.resultComponents.append(
                        self._getVideoComponent(shelfElement, shelfTitle=self._getShelfComponent(element)['title']))
            if richItemKey in element.keys() and findVideos:
                richItemElement = self._getValue(element, [richItemKey, 'content'])
                if videoElementKey in richItemElement.keys():
                    videoComponent = self._getVideoComponent(richItemElement)
                    self.resultComponents.append(videoComponent)
            if len(self.resultComponents) >= self.limit:
                break

class Search(SearchCore):
    def __init__(self, query: str, limit: int = 20, language: str = 'en', region: str = 'US', timeout: int = None):
        self.searchMode = (True, True, True)
        super().__init__(query, limit, language, region, None, timeout)
        self.sync_create()
        self._getComponents(*self.searchMode)

    def next(self) -> bool:
        return self._next()

class VideosSearch(SearchCore):
    def __init__(self, query: str, limit: int, language: str = 'en', region: str = 'US', timeout: int = None):
        self.searchMode = (True, False, False)
        super().__init__(query, limit, language, region, SearchMode.videos, timeout)
        self.sync_create()
        self._getComponents(*self.searchMode)

    def next(self) -> bool:
        return self._next()





class ChannelSearch(ChannelSearchCore):
    def __init__(self, query: str, browseId: str, language: str = 'en', region: str = 'US', searchPreferences: str = "EgZzZWFyY2g%3D", timeout: int = None):
        super().__init__(query, language, region, searchPreferences, browseId, timeout)
        self.sync_create()


class CustomSearch(SearchCore):
    def __init__(self, query: str, searchPreferences: str, limit: int = 20, language: str = 'en', region: str = 'US', timeout: int = None):
        self.searchMode = (True, True, True)
        super().__init__(query, limit, language, region, searchPreferences, timeout)
        self.sync_create()
        self._getComponents(*self.searchMode)
    
    def next(self):
        self._next()


init()

logger.remove()  # Удаляем стандартный обработчик
logger.add(sink=sys.stdout,
           format='<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>')


re_year = '"publishedAt": "(.*)",'
re_onlyyear= r'^(\d+)-'
re_email = '(?:[A-Za-z0-9!#$%&\'*+\\/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&\'*+\\/=?^_`{|}~-]+)*|\\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])'





class Engine():
    def __init__(self):
        check = requests.post('https://api.ytmailer.pro/index.php',data={'hwid':HWID})
        if check.status_code == 200:
            check = json.loads(check.text)
            if check['status'] == True:
                hwid_new = check['hwid']
                salt = 'ytsoft139392924992491dds'
                if (hashlib.md5((HWID+salt).encode())).hexdigest() != hwid_new:
                    sys.exit()
                else:
                    check_v = requests.post('https://api.ytmailer.pro/index.php',data={'hwid':HWID,'version':__version__}).json()
                    if check_v['status']:
                        logger.success(f'Найдена новая версия.. Обновляемся ({check_v["version"]})')
                        with open(f'YTparser-{check_v["version"]}.exe','wb') as file:
                            file.write(requests.get(check_v['url']).content)
                        os.system(f'YTparser-{check_v["version"]}.exe')
                        sys.exit()
            else:
                logger.info(f'Ваш HWID: {HWID}')
                logger.error('У вас нет подписки! Отправьте ваш HWID продавцу')
                input()
                sys.exit()

        else:
            logger.error('Сервер на тех. Работах. Нажмите любую кнопку!')
            input()
            sys.exit()

        self.apis = self.read_file("API.txt")
        self.keys = self.read_file("keywords.txt")
        self.blackwords = self.read_file("blackwords.txt")
        self.proxys = self.read_file('proxy.txt')
        self.emails = 0

        os.system('title "@wxkssy | Tg bot: @qualityshop24_bot"')

        
        num_threads = int(input(Fore.GREEN + '> Enter number of threads: ' + Style.RESET_ALL))
        self.videocount = 0
        
    
        while (True):
            self.year = input(Fore.GREEN + '> Enter max channel reg-year: ' + Style.RESET_ALL)
            if self.year.isdigit():
                self.year = int(self.year)
                if (self.year > 2000):
                    break
        while (True):
            self.views = input(Fore.GREEN + '> Enter min channel views: ' + Style.RESET_ALL)
            if self.views.isdigit():
                self.views = int(self.views)
                break

        while True:
            self.subs = input(Fore.GREEN + '> Enter min & max subs: ' + Style.RESET_ALL)
            if not '-' in self.subs:
                self.subs = input(Fore.GREEN + '> Enter min & max subs: ' + Style.RESET_ALL)
                
            else:
                self.subs = [int(self.subs.split('-')[0]), int(self.subs.split('-')[1])]
                if (self.subs[0] < self.subs [1]):
                    break

        self.blacklist = input(Fore.GREEN + '> Enter blacklist (y/n): ' + Style.RESET_ALL)
        if self.blacklist.lower() != 'y':
            self.blackwords = ''

        logger.info(f'Max Year: {self.year} | Min Views: {self.views} | Subs: {self.subs[0]}-{self.subs[1]}')
        sleep(1)
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=self.process_data)
            threads.append(t)
        
        for t in threads:
            t.start()

        threading.Thread(target=self.console_log).start()

        for t in threads:
            t.join()

        logger.info('Данные закончились, завершение...')
        input("Нажми ENTER, чтобы завершить")


    def read_file(self,filename):
        with open(filename, 'r',encoding='utf-8',errors='ignore') as f:
            return f.read().split('\n')



    def process_data(self):

            
        proxies = {
            'http': f'http://{random.choice(self.proxys)}',
        }
        while True:
            try:
                if self.apis == [] or self.keys == []:
                    break
                api = random.choice(self.apis)
                key = random.choice(self.keys)

                search = VideosSearch(key, limit=50)
                try:
                    self.keys.remove(str(key))
                except:
                    pass
                videoIds = search.result()

                while True:
                    try:
                        for videoID in videoIds['result']:                            

                            description = ''
                            if videoID['descriptionSnippet'] != None:
                                for _ in videoID['descriptionSnippet']:
                                    description += _['text'] + ' '
                            email = re.findall(re_email, description)

                            channelId = videoID['channel']['id']

                            while True:
                                try:
                                    api = random.choice(self.apis)
                                    resp = requests.get(f'https://www.googleapis.com/youtube/v3/channels?part=statistics%2Csnippet&maxResults=50&id={channelId}&key={str(api)}',proxies=proxies)
                                    if resp.status_code == 200:
                                        resp_rez = resp.json()["items"][0]
                                        break
                                    else:
                                        try:
                                            self.apis.remove(api)
                                        except:
                                            pass
                                        if self.apis == []:
                                            break
                                except:
                                    proxies = {
                                        'http': f'http://{random.choice(self.proxys)}',
                                    }
                            if self.apis == []:
                                return
                            while True:
                                try:
                                    vid = videoID['id']
                                except:
                                    res3 = []
                                    break
                                try:
                                    api = random.choice(self.apis)
                                    resp = requests.get(f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet&part=contentDetails&part=statistics&id={vid}&key={api}",proxies=proxies)
                                    if resp.status_code == 200:
                                        res3 = re.findall(re_email, resp.text.replace(r"\n", ""))
                                        break
                                    else:
                                        try:
                                            self.apis.remove(api)
                                        except:
                                            pass
                                        if self.apis == []:
                                            break
                                except:
                                    proxies = {
                                        'http': f'http://{random.choice(self.proxys)}',
                                    }
                            if self.apis == []:
                                return

                            yearid = int(resp_rez['snippet']['publishedAt'][:4])
                            # Количество подписчиков
                            try:
                                subscount = resp_rez["statistics"]["subscriberCount"]
                            except Exception:
                                subscount = 0

                            try:
                                viewscount = resp_rez["statistics"]["viewCount"]
                            except:
                                viewscount = 0

                            try:
                                countryId = resp_rez["snippet"]["country"]
                            except Exception:
                                countryId = 'Not'
                            if countryId in self.blackwords:
                                pass
                            else:
                                if res3 != []:
                                    if self.year >= int(yearid):
                                        if self.subs[0] <= int(subscount) and self.subs[1] >= int(subscount):
                                            if self.views <= int(viewscount):
                                                for mail in res3:
                                                    self.write_mail(f"emails.txt", mail)

                                if email != []:
                                    if self.year >= int(yearid):
                                        if self.subs[0] <= int(subscount) and self.subs[1] >= int(subscount):
                                            if self.views <= int(viewscount):
                                                for mail in email:
                                                    self.write_mail(f"emails.txt", mail)
                                # описание канала
                                try:
                                    descriptionCN = resp_rez["snippet"]["description"]
                                except Exception:
                                    descriptionCN = ''
                                emailDesc = re.findall(re_email, descriptionCN)
                                if emailDesc != []:
                                    if self.year >= int(yearid):
                                        if self.subs[0] <= int(subscount) and self.subs[1] >= int(subscount):
                                            if self.views <= int(viewscount):
                                                for mail in emailDesc:
                                                    self.write_mail(f"emails.txt", mail)
                            self.videocount += 1
                        try:
                            search.next()
                            videoIds = search.result()
                        except:
                            break
                        nextpage = len(videoIds['result'])
                        if nextpage == 0:
                            break
                    except:
                        pass
            except:
                pass



    def write_mail(self,filename, data):
        x = self.read_file(filename)
        with open(filename, 'a+',encoding='utf-8') as f:
            if data not in x:
                f.write(str(data) + '\n')
                self.emails += 1

    def console_log(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            logger.info(f'ApiKeys: {len(self.apis)} | KeyWords: {len(self.keys)} | Emails: {self.emails} | Video_seen: {self.videocount}')
            sleep(5)




Engine()