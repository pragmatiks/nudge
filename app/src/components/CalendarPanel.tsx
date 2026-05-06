import "temporal-polyfill/global";
import { useEffect, useState } from "react";
import {
  createViewDay,
  createViewList,
  createViewMonthGrid,
  createViewWeek,
  type CalendarEventExternal,
} from "@schedule-x/calendar";
import { createEventsServicePlugin } from "@schedule-x/events-service";
import { createCalendarControlsPlugin } from "@schedule-x/calendar-controls";
import { ScheduleXCalendar, useCalendarApp } from "@schedule-x/react";
import "@schedule-x/theme-default/dist/index.css";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDataStore } from "../store/dataStore";
import type { CalendarEvent } from "../types/protocol";

type SxViewName = "list" | "day" | "week" | "month-grid";

const VIEWS: { id: SxViewName; label: string }[] = [
  { id: "list", label: "List" },
  { id: "day", label: "Day" },
  { id: "week", label: "Week" },
  { id: "month-grid", label: "Month" },
];

/** Parse an ISO datetime as a ZonedDateTime in the local TZ.
 * Accepts offset/Z-suffixed strings (treated as instants) and offset-less
 * `YYYY-MM-DDTHH:mm[:ss]` strings (treated as local wall-clock time).
 */
function toLocalZdt(iso: string, tz: string) {
  // ends with Z, ±HH:MM, or ±HHMM → has an offset, parse as instant
  if (/(?:Z|[+-]\d{2}:?\d{2})$/.test(iso)) {
    return Temporal.Instant.from(iso).toZonedDateTimeISO(tz);
  }
  return Temporal.PlainDateTime.from(iso).toZonedDateTime(tz);
}

/** Convert a stored CalendarEvent (ISO strings) to schedule-x Temporal format. */
function toSxEvent(e: CalendarEvent): CalendarEventExternal {
  if (e.all_day) {
    return {
      id: e.id,
      title: e.title,
      start: Temporal.PlainDate.from(e.start.slice(0, 10)),
      end: Temporal.PlainDate.from(e.end.slice(0, 10)),
      description: e.description || undefined,
      location: e.location || undefined,
    };
  }
  const tz = Temporal.Now.timeZoneId();
  return {
    id: e.id,
    title: e.title,
    start: toLocalZdt(e.start, tz),
    end: toLocalZdt(e.end, tz),
    description: e.description || undefined,
    location: e.location || undefined,
  };
}

export function CalendarPanel() {
  const events = useDataStore((s) => s.events);
  const [view, setView] = useState<SxViewName>("list");

  const eventsService = useState(() => createEventsServicePlugin())[0];
  const calendarControls = useState(() => createCalendarControlsPlugin())[0];

  const calendar = useCalendarApp({
    views: [createViewList(), createViewDay(), createViewWeek(), createViewMonthGrid()],
    defaultView: "list",
    isDark: true,
    locale: "en-GB",
    firstDayOfWeek: 1,
    // Trim the time-grid to working/waking hours so events stay in view on a 700px-tall window.
    dayBoundaries: { start: "07:00", end: "22:00" },
    weekOptions: {
      nDays: 5,
      timeAxisFormatOptions: { hour: "2-digit", minute: "2-digit", hour12: false },
    },
    plugins: [eventsService, calendarControls],
  });

  // Replace schedule-x's event list whenever the Zustand events change.
  useEffect(() => {
    eventsService.set(events.map(toSxEvent));
  }, [events, eventsService]);

  useEffect(() => {
    calendarControls.setView(view);
  }, [view, calendarControls]);

  return (
    <Tabs
      value={view}
      onValueChange={(v) => setView(v as SxViewName)}
      className="flex flex-col h-full min-h-0 gap-0"
    >
      <TabsList className="shrink-0 w-full mx-3 mt-2 mb-0 self-stretch">
        {VIEWS.map(({ id, label }) => (
          <TabsTrigger key={id} value={id}>
            {label}
          </TabsTrigger>
        ))}
      </TabsList>

      <div className="flex-1 min-h-0 sx-react-calendar-wrapper mt-2">
        <ScheduleXCalendar calendarApp={calendar} />
      </div>
    </Tabs>
  );
}
