import datetime, re
import googleapiclient.discovery
import google.auth
import env

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    gapi_creds = google.auth.load_credentials_from_file("credentials.json", SCOPES)[0]
    service = googleapiclient.discovery.build("calendar", "v3", credentials=gapi_creds)

    target_start_dt = (datetime.datetime(2021, 2, 1)).isoformat() + "Z"
    target_end_dt = (datetime.datetime(2022, 11, 30)).isoformat() + "Z"

    event_list = (
        service.events()
        .list(
            calendarId=env.TARGET_CALENDAR_ID,
            timeMin=target_start_dt,
            timeMax=target_end_dt,
            maxResults=2500,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = event_list.get("items", [])
    print(f"総イベント数: {len(events)}\n")

    formatted_events = [
        dict(
            start_dt=event["start"]["dateTime"],
            end_dt=event["end"]["dateTime"],
            summary=event.get("summary", "名称未設定"),
        )
        for event in events
        if "dateTime" in event["start"] and "dateTime" in event["end"]
    ]
    print(f"一日のイベントを除いた総イベント数: {len(formatted_events)}\n")

    # 一日以上のイベントを抽出
    one_day_events = [
        dict(
            start_dt=event["start"]["date"],
            end_dt=event["end"]["date"],
            summary=event.get("summary", "名称未設定"),
        )
        for event in events
        if "dateTime" not in event["start"] or "dateTime" not in event["end"]
    ]
    print(f"一日のイベント: {one_day_events}\n")

    # 時間をフォーマット
    for event in sorted(formatted_events, key=lambda x: len(x["summary"])):
        start_dt = datetime.datetime.fromisoformat(event["start_dt"])
        end_dt = datetime.datetime.fromisoformat(event["end_dt"])
        event["start_dt"] = start_dt
        event["end_dt"] = end_dt
        event["duration"] = end_dt - start_dt

    # 表記ゆれの統一  # FIXME: 精度
    analysis = dict()
    for event in formatted_events:
        for analysis_key in analysis.keys():
            if analysis_key in event["summary"]:
                analysis[analysis_key] += event["duration"]
                break
        else:
            analysis[event["summary"]] = (
                analysis[event["summary"]] + event["duration"]
                if analysis.get(event["summary"])
                else event["duration"]
            )

    # 累計時間の降順にソート
    sorted_analysis = sorted(analysis.items(), key=lambda x: x[1], reverse=True)
    for summary, duration in sorted_analysis:
        print(f"{summary}: {duration}")

    # 累計時間の合計
    sum = datetime.timedelta(seconds=0)
    for event in formatted_events:
        sum += event["duration"]
    print(f"合計:  {sum} ({sum / datetime.timedelta(hours=1)}[hours])")


if __name__ == "__main__":
    main()
