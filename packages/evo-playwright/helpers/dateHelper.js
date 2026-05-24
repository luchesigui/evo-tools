/**
 * Calculates the date range (de domingo a sábado) for the previous complete week
 * relative to the provided base date (defaults to current date).
 * 
 * @param {Date} [relativeDate] Base date to calculate relative to
 * @returns {{ de: Date, ate: Date }} Date range representing Sunday and Saturday of the last week
 */
export function getLastWeekRange(relativeDate = new Date()) {
  const base = new Date(relativeDate);
  const currentDay = base.getDay(); // 0 (Sunday) to 6 (Saturday)

  // Sunday of last week: base date minus current day of the week minus 7 days
  const de = new Date(base);
  de.setDate(base.getDate() - currentDay - 7);
  de.setHours(0, 0, 0, 0);

  // Saturday of last week: base date minus current day of the week minus 1 day
  const ate = new Date(base);
  ate.setDate(base.getDate() - currentDay - 1);
  ate.setHours(23, 59, 59, 999);

  return { de, ate };
}
