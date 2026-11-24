const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

// Exercise form submission wiring without adding a DOM dependency. Layout and
// native dialog behavior still require a real browser review.
function app(response) {
  const elements = new Map();
  const requests = [];
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value: '', disabled: false, hidden: false, elements: [], handlers: {},
      addEventListener(type, callback) { this.handlers[type] = callback; },
      setAttribute() {}, focus() {}, reset() { this.wasReset = true; },
    });
    return elements.get(id);
  }
  const context = vm.createContext({
    document: { getElementById: element, querySelector: () => element('skip') },
    window: { addEventListener() {} }, location: { hash: '' }, AbortSignal,
    fetch: async (url, options) => {
      requests.push({ url, ...options });
      return { status: 201, ok: true, json: async () => response };
    },
  });
  const source = readFileSync(path.join(__dirname, '../../frontend/assets/app.js'), 'utf8');
  vm.runInContext(source.replace(/restoreSession\(\);\s*$/, ''), context);
  vm.runInContext('renderRoute = async () => {}; accessCodeSheet = () => { codePresented = true; };', context);
  return { context, element, requests };
}

test('personal sign-in sends a POST, prevents navigation and restores the server name', async () => {
  const a = app({ profileId: 'p-test', displayName: 'Lucía', role: 'listener' });
  a.element('personal-code').value = '  generated-test-code  ';
  let prevented = false;
  assert.equal(typeof a.element('personal-login-form').handlers.submit, 'function');
  await a.element('personal-login-form').handlers.submit({ preventDefault() { prevented = true; } });
  assert.ok(prevented);
  assert.equal(a.requests[0].url, '/api/v1/sessions');
  assert.equal(a.requests[0].method, 'POST');
  assert.deepEqual(JSON.parse(a.requests[0].body), { code: 'generated-test-code' });
  assert.equal(a.element('profile-name').textContent, 'Lucía');
  await vm.runInContext('(async () => showAccount(await api(paths.session)))()', a.context);
  assert.equal(a.element('profile-name').textContent, 'Lucía');
  assert.equal(a.element('editor-link').hidden, true);
});

test('creation sends only a name and presents the server access code before continuing', async () => {
  const a = app({ profileId: 'p-test', displayName: 'Lucía', role: 'listener', accessCode: 'test-only', graphPending: false });
  a.element('display-name').value = 'Lucía';
  let prevented = false;
  await a.element('create-profile-form').handlers.submit({ preventDefault() { prevented = true; } });
  assert.ok(prevented);
  assert.equal(a.requests[0].url, '/api/v1/profiles');
  assert.deepEqual(JSON.parse(a.requests[0].body), { displayName: 'Lucía' });
  assert.equal(a.element('profile-name').textContent, 'Lucía');
  assert.equal(a.context.codePresented, true);
  assert.equal(a.element('create-submit').disabled, false);
});
