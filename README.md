# Busiest-Climbers-UKC

This script scrapes the website UKClimbing.com to collect user data and collate it into leaderboards of who has completed the most climbs in an area.

UKClimbing.com is a website where climbers can log which climbs they have done at a crag (outdoor climbing area).
This data is displayed on individual web pages for each climb in the area as:
*Usernames,
*Whether they completed the climb clean (in one go from the ground),
*The style (lead, top rope, soloing, etc),
*Any comments they have


This data can only be viewed if you log on, so the first step is the script logs on to the site using Selenium, with an account made specifically for this program.
Once logged in, the script loads the crag web page which has a list of climbs in that crag. This list is rendered by the web page using Javascript which takes
a few seconds to load, Selenium is again used to scrape the data from the rendered site.

The next step is to load each climbs' web page and scrape the user data. This is saved to a dictionary of climbers (saved as keys by username) and the climbs they
have done clean (saved as a list of climb names). Once each crag has been scraped, the climbers are put into a top ten leaderboard of who has completed the most
climbs in that area. This is assembled by sorting the dictionary keys by length of their list value. A percentage completed comes from (length of list of completed
climbs) / (the total number of climbs in the area). This leaderboard is then printed to a txt file.

This can be done for an entire region. Climbing guidebooks have a list of crags, and the crags they cover are listed on another web page within UKClimbing.com.
The user makes a choice whether to scrape an entire region through this list once starting the script. If they do, the script is run for each crag in turn, however
once all the crags have been scraped, a leaderboard for the entire region is printed to a txt file, as well as leaderboards for all the crags.
