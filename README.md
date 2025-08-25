# SafariPrivateHistoryParser
Grabs BLOBs from SafariTabs.db to get history data stored in the local bookmarks.local_attributes, which stores BPlists as BLOB data.

#### * * * There is still more work, testing, and validation to do on this, but due to a lack of time, I'm putting out this simple script for awareness. Manual review of db data and primary bplist data should still be done. If you have any info to add, please reach out.***

The <b>SarfariTabs.db</b> database contains information about active private browser tabs that are still open on the device within the bookmarks table. The bookmarks.parent column will identify what tabs are open in the Private mode, using an identified value (e.g., "6"). The bookmarks.title column will identify the title of the active webpage, while the bookmarks.url column provides its namesake. The bookmarks.title column also includes values of “pinned, privatePinned, recentlyClosed, Windows, Local, and Private.” The bookmarks.num_children column shows the number of tabs assigned to those values, for example how many private or local (non-private) browser tabs are open.

So how can an examiner identify some of that browser history data that our tools may be missing? Moving to the <b>bookmarks.extra_attributes</b> column, we find BPlists that are stored as BLOB data. These BPlists provide information about the open tab, such as the URL, webpage title, and importantly, the LastDateViewed tab, showing when that tab was last viewed/active by the user. 

Next, we have the <b>bookmarks.local_attributes</b> column, which again have BPlists that are stored as BLOB data. These Plists contains information about that tab again, including system information about the tab, such as if the webpage being a bookmark, if it was opened from a link, or even if it is Reader mode. The <b>SessionState</b> key, however, is where we find the most useful data, stored as yet another BPlist that contains the history for that tab.

This Plist contains a few more keys and subkeys that can be worked through. The SessionHistoryCurrentIndex value will show the number of entries that are stored in the tab’s history, while the SessionHistroyEntries values will show the URLs (SessionHistoryEntryURL and SessionHistoryEntryOriginalURL) and webpage titles (SessionHistoryEntryTitle) that are stored within the history of the tab. Viewing this data, examiners can view browser history, searches that have been completed, and even associate a time to them for that tab.

Going further, if there are Google searches or other URLs that contain a timestamp in the session history entries, using tools like [Unfurl](https://dfir.blog/unfurl/) can help quickly decode those URLs to identify the time when searches were completed and produce a timeline to the user’s internet activity.
Private browsers are a great way for users to limit tracking or hide activity. However, if users are leaving their private open, examiners have an opportunity to find data of the user’s internet activities which they may have believed were not stored or tracked.

