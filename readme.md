# HomeHub V2

This is the API for an improved version of **HomeHub** flask version.

> This version of HomeHub is based on Django

## Main modules in this API
* Upload
* Library
* Labels
* Search
* Recommendations

## Upload
The purpose of this module is to upload new videos to the server

The user is able to do both bulk uploading or single file uploading and the labels set by the user will be included into every video in the bulk.

The user is able to upload video files longer than **15 seconds** using this module.

In order to use this module, the user should **"POST"** a request to the *"/upload"* URL with a body containing the files and the labels.

### Request body
The files that is needed to be uploaded and the relevant labels of the currently uploading files are here.

#### The allowed keys are listed below
* file - Includes single or multiple video files that is needed to be uploaded
* labels - The labels that is needed to be set for the currently uploading files.

> The user can set multiple labels for the files by repeating label parameter in the request body
> 
> Example: If you want to set "Action" and "Thriller" labels to the video that you are currently uploading,
> 
> * Key = "Labels"    Value = "Action"
> * Key = "Labels"    Value = "Action"
> 

### Return values
This URL will return a JSON that contains the names of the failed files

### Failed files
The following conditions will prevent the files from uploading
* The file is not a video file.
* The file is unable to parse. (This could happen if the file is corrupt or the file is not compatible with HomeHub)

## Library
This URL will enable the user to get the videos in the server. In order to access this module, the users should do **"GET"** requests to the *"/library"* URL.

### URL methods
By directly executing the *"/library"* URL, the user can get every video in the server with a JSON file.

Users can do pagination with the results by using the "page" parameter.

#### Parameters
The allowed parameters are listed below
* page - Sets the current page number
* max - Sets the maximum amount of videos per page

### Return values
This module will return all the videos in the server when executed standalone. 

Will return the relevant videos in the respective page and the maximum page number if the page number is given

> The default number of items per page is 15

## Labels
A video can have one or more videos. A label defines the characteristics of a video, and it will enable the users to categorize videos based on their characteristics. 

#### Labels are used to:
* Categorize videos depending on their characteristics
* Search for videos with a certain label
* Generating recommendations for the user
* Filter search results

### Working with the Label API
Accessing *"/labels"* directly will return a list of labels that is currently created in the HomeHub server.
Users will be enabled to,
* Remove unused labels
* Change the labels of a video
* Add new labels to a videos 
* Add new labels to the database

#### Parameters in Labels module
* "remove" - Removes the given label if it is not used.
* "video-id" - The id of the video that the ids to be changed.
* "labels" - The labels that is needed to be assigned to the video.

> **Note:** Just using the 'video-id' parameter without the labels parameter will remove any labels associated with the video

## Search
This module will enable the user to search videos using 
* A search query
* Label
* or both

In order to begin a search one or both of the following parameters must be given
* q - Search query should be given to this parameter
* filter - The labels that is needed to filter the search results must be given to this parameter

> This module is not usable standalone and one or both of the above parameters should be used

## Recommendations
This module will generate maximum 6 recommendations for the users. The recommendations are based on the total views that each module has

In order to use this module, the user have to use *"/recom"* route.
