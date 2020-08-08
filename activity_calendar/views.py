from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_safe

from .models import Activity

# Renders the simple v1 calendar
@require_safe
def googlehtml_activity_collection(request):
    return render(request, 'activity_calendar/calendar.html', {})


# Renders the calendar page, which utilises FullCalendar
@require_safe
def activity_collection(request):
    # all_events = Events.objects.all()

    # if request.GET:  
    #     event_arr = []

    #     for i in all_events:
    #         event_sub_arr = {}
    #         event_sub_arr['title'] = i.event_name
    #         start_date = datetime.datetime.strptime(str(i.start_date.date()), "%Y-%m-%d").strftime("%Y-%m-%d")
    #         end_date = datetime.datetime.strptime(str(i.end_date.date()), "%Y-%m-%d").strftime("%Y-%m-%d")
    #         event_sub_arr['start'] = start_date
    #         event_sub_arr['end'] = end_date
    #         event_arr.append(event_sub_arr)
    #     return HttpResponse(json.dumps(event_arr))

    context = {
        # "events":all_events,
    }
    return render(request, 'activity_calendar/fullcalendar.html', context)

def get_activity_json(activity, start, end):
    return {
        'groupId': activity.id,
        'title': activity.title,
        'description': activity.description,
        'location': activity.location,
        'recurrenceInfo': {
            'rrules': [rule.to_text() for rule in activity.recurrences.rrules],
            'exrules': [rule.to_text() for rule in activity.recurrences.exrules],
            'rdates': [occ.date().isoformat() for occ in activity.recurrences.rdates],
            'exdates': [occ.date().isoformat() for occ in activity.recurrences.exdates],
        },
        'start': start,
        'end': end,
        'allDay': False,
    }

@require_safe
def fullcalendar_feed(request):
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)
    test = request.GET.get('test', None)

    # Start and end dates should be provided
    if start_date is None or end_date is None:
        return HttpResponseBadRequest("start and end date must be provided")

    # Start and end dates should be provided in ISO format
    try: 
        start_date = datetime.fromisoformat(start_date)
        end_date = datetime.fromisoformat(end_date)
    except ValueError:
        return HttpResponseBadRequest("start and end date must be in yyyy-mm-ddThh:mm:ss+hh:mm format")
    
    # Start and end dates cannot differ more than a 'month' (7 days, 6 weeks)
    if (end_date - start_date).days > 42:
        return HttpResponseBadRequest("start and end date cannot differ more than 42 days")

    # Obtain non-recurring activities
    activities = []
    non_recurring_activities = Activity.objects.filter(recurrences="", published_date__lte=timezone.now()) \
            .filter((Q(start_date__gte=start_date) | Q(end_date__lte=end_date)))
    
    for non_recurring_activity in non_recurring_activities:
        activities.append(get_activity_json(
            non_recurring_activity,
            non_recurring_activity.start_date.isoformat(),
            non_recurring_activity.end_date.isoformat()
        ))

    # Obtain occurrences of recurring activities in the relevant timeframe
    all_recurring_activities = Activity.objects.exclude(recurrences="").filter(published_date__lte=timezone.now())

    for recurring_activity in all_recurring_activities:
        recurrences = recurring_activity.recurrences
        start_time = recurring_activity.start_date.time()
        end_time = recurring_activity.end_date.time()

        # If the activity ends on a different day than it starts, this also needs to be the case for the occurrence
        days_diff = recurring_activity.end_date.date() - recurring_activity.start_date.date()

        for occurence in recurrences.between(start_date, end_date, dtstart=recurring_activity.start_date, inc=True):
            occurence_start_date = datetime.combine(occurence.date(), start_time, tzinfo=timezone.utc)
            activities.append(get_activity_json(
                recurring_activity,
                occurence_start_date.isoformat(),
                datetime.combine(occurence.date() + days_diff, end_time, tzinfo=timezone.utc).isoformat()
            ))

    return JsonResponse({'activities': activities})


# https://stackoverflow.com/questions/8858426/fullcalendar-json-feed-caching
# https://fullcalendar.io/docs/recurring-events
