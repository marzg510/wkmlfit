from step_getter import StepGetter
from oauth2client import client
from oauth2client.file import Storage
import httplib2
from apiclient.discovery import build

class GoogleFitStepGetter(StepGetter):
    def __init__(self,credential_file):
        # Googleのcredential読み込み
        storage = Storage(credential_file)
        self.credentials = storage.get()
        self.http_auth = self.credentials.authorize(httplib2.Http())
        self.request = build('fitness', 'v1', http=self.http_auth)
    def get_step(self,target_date):
        from datetime import timedelta,datetime
        import time as t
        targetStartTimeMillis=int(t.mktime(target_date.timetuple()))*1000
        targetEndTimeMillis=int(t.mktime((target_date + timedelta(days=1)).timetuple()))*1000 
        # request bodyの作成
        body = {
          "aggregateBy": [
            {
              "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }
          ],
          "startTimeMillis": targetStartTimeMillis,
          "endTimeMillis": targetEndTimeMillis,
          "bucketByTime": {
            "durationMillis": "86400000"
          }
        }
        # データの取得
        buckets = self.request.users().dataset().aggregate(userId='me',body=body).execute()
        # 歩数の取り出し
        for i,bucket in enumerate(buckets['bucket']):
#            print('[{}] {}'.format(i,bucket))
            startTime = datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000)
            endTime = datetime.fromtimestamp(int(bucket['endTimeMillis'])/1000)
#            print('startTime:{},endTime:{}'.format(startTime,endTime))
            for j,dataset in enumerate(bucket['dataset']):
                if 'point' in dataset:
                    for point in dataset['point']:
#                        print('  [{}] {}'.format(j,point))
                        for k,v in enumerate(point['value']):
#                            print('    [{}] start:{} end:{} value:{}'.format(k,datetime.fromtimestamp(int(point['startTimeNanos'])/1000/1000/1000),
#                                  datetime.fromtimestamp(int(point['endTimeNanos'])/1000/1000/1000),
#                                  v))
                            step = int(v['intVal'])
                            break
                        break
                    break
            break
        return step

