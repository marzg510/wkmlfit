import random_step
import googlefit_step
from datetime import datetime,date,time

s = random_step.RandomStepGetter(5000,10000)
print('random step:{}'.format(s.get_step('')))

s = googlefit_step.GoogleFitStepGetter('./googlefit_credential')
target_date = datetime.combine(date(2019,5,4),time(0))
print('google step({}):{}'.format(target_date,s.get_step(target_date)))
