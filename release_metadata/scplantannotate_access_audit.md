# scPlantAnnotate Access Audit

- Base URL: `https://scplantannotate.missouri.edu/`
- Web server reachable: `True`
- Root HTTP status: `200`
- Assets discovered: `5`
- Assets fetched: `8`
- API/upload terms detected: `True`
- Scriptable batch API detected: `False`
- Endpoint probes: `3`
- Anonymous API accessible: `False`
- Auth-required endpoint count: `3`
- Reproducible comparison ready: `False`

## Interpretation

A reachable web front end and discoverable API route are not enough for a reproducible benchmark if the routes require an authenticated session. SnowLotus-CellFM should keep scPlantAnnotate comparison missing unless valid credentials, a scriptable guest API, a CLI, official model weights, or an author-provided result export path is available.

## Candidate URL Literals

- `/>
    <link rel=`
- `/>
    <meta name=`
- `/@react-refresh`
- `/@vite/client`
- `/index.html`
- `/logo.jpeg`
- `/logo192.png`
- `/manifest.json`
- `/node_modules/.vite/deps/chunk-APAI5QCZ.js?v=7de1c5b0`
- `/node_modules/.vite/deps/chunk-F554S2KQ.js?v=7de1c5b0`
- `/node_modules/.vite/deps/chunk-PR4QN5HX.js?v=7de1c5b0`
- `/node_modules/.vite/deps/react-dom_client.js?v=7de1c5b0`
- `/node_modules/.vite/deps/react.js?v=7de1c5b0`
- `/node_modules/.vite/deps/react_jsx-dev-runtime.js?v=7de1c5b0`
- `/node_modules/vite/dist/client/env.mjs`
- `/src/App.jsx`
- `/src/index.css`
- `/src/index.jsx`
- `/src/reportWebVitals.js`
- `/usr/src/app/src/index.jsx`
- `http://vite.dev`
- `https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap`
- `https://react.dev/link/hydration-mismatch`

## Endpoint Probes

- `/api/jobs/api/job_annotate_and_plot_query/` status `403` anonymous `False` auth_required `True`
- `/api/organisms/api/organism_query/` status `403` anonymous `False` auth_required `True`
- `/api/predictors/api/predictor_query_public/` status `403` anonymous `False` auth_required `True`

## Keyword Lines

- `"%s has a method called componentDidReceiveProps(). But there is no such lifecycle method. If you meant to update the state in response to changing props, use componentWillReceiveProps(). If you meant to fetch data or run side-effects or mutations after React has updated the UI, use componentDidUpda`
- `"%s uses the legacy childContextTypes API which was removed in React 19. Use React.createContext() instead. (https://react.dev/link/legacy-context)",`
- `"%s uses the legacy contextTypes API which was removed in React 19. Use React.createContext() with React.useContext() instead. (https://react.dev/link/legacy-context)",`
- `"%s uses the legacy contextTypes API which was removed in React 19. Use React.createContext() with static contextType instead. (https://react.dev/link/legacy-context)",`
- `"%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)",`
- `"Hydration failed because the server rendered " + (fromText ? "text" : "HTML") + " didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:\n\n- A server/client branch `if (typeof window !== 'undefined')`.\n- Variable input `
- `"The result of getServerSnapshot should be cached to avoid an infinite loop"`
- `"The result of getSnapshot should be cached to avoid an infinite loop"`
- `case "download":`
- `const result = await transport$1.invoke({`
- `const { error, result } = data.data;`
- `else promise.resolve(result);`
- `fetch(new URL(`${base$1}__open-in-editor?file=${encodeURIComponent(file)}`, import.meta.url));`
- `for (var i = 0; i < listeners.length; i++) (0, listeners[i])(result);`
- `function chainThenableValue(thenable, result) {`
- `function startHostTransition(formFiber, pendingState, action, formData) {`
- `if (!(err instanceof Error) || !err.message.includes("fetch")) this.logger.error(err);`
- `if ("error" in result) throw reviveInvokeError(result.error);`
- `return action(formData);`
- `return result.result;`
- `thenableWithOverride.value = result;`
