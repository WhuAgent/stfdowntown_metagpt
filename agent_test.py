class TestScratch:
    def __init__(self):
        self.iss = "Name: Maria Lopez\nAge: 21\nInnate traits: energetic, enthusiastic, inquisitive\nLearned traits: Maria Lopez is a student at Oak Hill College studying physics and a part time Twitch game streamer who loves to connect with people and explore new ideas.\nCurrently: Maria Lopez is working on her physics degree and streaming games on Twitch to make some extra money. She visits Hobbs Cafe for studying and eating just about everyday.\nLifestyle: Maria Lopez goes to bed around 2am, awakes up around 9am, eats dinner around 6pm. She likes to hang out at Hobbs Cafe if it's before 6pm.\nDaily plan requirement: Maria Lopez spends at least 3 hours a day Twitch streaming or gaming.\nCurrent Date: Monday February 13\n"
        self.lifestyle = "Maria Lopez goes to bed around 2am, awakes up around 9am, eats dinner around 6pm. She likes to hang out at Hobbs Cafe if it's before 6pm."
        self.firstname = 'Maria'
        self.curr_date = "Monday February 13"
        self.daily_req: list[str] = []
    
    def get_str_iss(self):
        return self.iss
    
    def get_str_lifestyle(self):
        return self.lifestyle
    
    def get_str_firstname(self):
        return self.firstname
    
    def get_str_curr_date_str(self):
        return self.curr_date

class TestRole:
    def __init__(self):
        self.scratch = TestScratch()