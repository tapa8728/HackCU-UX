import tweepy
import sys
import TOKENS
class TweetAPI(object):  
  def __init__(self):
    self.consumer_key = TOKENS.consumer_key
    self.consumer_secret = TOKENS.consumer_secret
    self.access_token=TOKENS.access_token
    self.access_token_secret=TOKENS.access_token_secret
    self.tweetlist=[]
    self.numb=0


  def postTweet(self,tweet):
    self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
    self.auth.set_access_token(self.access_token, self.access_token_secret)
    self.api = tweepy.API(self.auth,wait_on_rate_limit=True,wait_on_rate_limit_notify=True,timeout=5)
    self.api.update_status(tweet)
'''
tweets =  TweetAPI()
tweets.Connect()
tweets.postTweet("TWEETING from hackathon!!!")
'''
