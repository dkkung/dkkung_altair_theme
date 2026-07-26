// Scale a rendered chart by resizing its <svg> natively, instead of CSS `zoom` on the wrapper.
//
// dysonsphere charts are authored at the library's publication defaults (100x100 px, small
// fonts/marks), so the site scales the whole render up uniformly. That used to be
// `zoom: var(--ds-chart-zoom)` on the vega-embed wrapper. Firefox mis-maps SVG gradients inside
// a zoomed subtree: a continuous legend's colour bar sampled only the top ~15% of its ramp (an
// australis bar rendered green->cyan with no purple or blue), while the marks beside it were
// correct because they carry flat per-element fills. Chromium and WebKit are unaffected, so it
// looked like a spec bug rather than a rendering one.
//
// Vega's SVG carries a viewBox, so setting width/height scales it natively - no CSS scaling in
// the tree at all, gradients resolve correctly in every engine, and the layout box follows the
// render (which `transform: scale()` would not do). The viewBox is the source of truth for the
// natural size, so re-applying never compounds.
//
// The factor still comes from the --ds-chart-zoom custom property, so every per-context override
// (the landing hero, the palette preview) keeps working unchanged.

/** Natural (unscaled) size from the chart's viewBox, or null if it has not rendered yet. */
export function chartNaturalSize(el: HTMLElement): { svg: SVGSVGElement; width: number; height: number } | null {
	const svg = el.querySelector('svg');
	if (!svg) return null;
	const box = svg.viewBox?.baseVal;
	if (!box || box.width <= 0 || box.height <= 0) return null;
	return { svg, width: box.width, height: box.height };
}

/** Scale the chart by `factor`, defaulting to the element's computed --ds-chart-zoom. */
export function scaleChart(el: HTMLElement, factor?: number): void {
	const natural = chartNaturalSize(el);
	if (!natural) return;
	const zoom = factor ?? parseFloat(getComputedStyle(el).getPropertyValue('--ds-chart-zoom'));
	if (!(zoom > 0)) return;
	natural.svg.setAttribute('width', String(natural.width * zoom));
	natural.svg.setAttribute('height', String(natural.height * zoom));
}

/** Scale the chart so it spans `available` px wide (size-matched comparisons). */
export function fitChartToWidth(el: HTMLElement, available: number): void {
	const natural = chartNaturalSize(el);
	if (!natural || available <= 0) return;
	scaleChart(el, available / natural.width);
}
