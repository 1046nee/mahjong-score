// アカウントの試合一覧（mylists）のルールを、Firebase のエミュレーターで確かめる（本番DBには触らない）。
// 使い方（初回だけ準備）:
//   npm i --prefix /tmp/fbtest firebase-tools@15.34.0 @firebase/rules-unit-testing@4 firebase@11
//   npx --prefix /tmp/fbtest firebase emulators:exec --only database --project demo-majasco \
//     "NODE_PATH=/tmp/fbtest/node_modules node tools/mylist_rules_test.js"
// 2026-10-24: 一覧は持ち主（owner）だけが書ける・項目は消せない（削除は deleted の印だけ）にした
const fs = require('fs');
const path = require('path');
const { initializeTestEnvironment, assertSucceeds, assertFails } = require('@firebase/rules-unit-testing');

const LID = 'ABCDEFGHJKLMNP';   // 14文字（リストID）
const LID2 = 'QRSTUVWXYZabcd';
const OLD = 'efghjkmnpqrstu';   // 持ち主の無い古いリスト（引き継ぎURLの時代のもの）
const GID = 'ABCDEFGHJK';       // 10文字（試合ID）
const GID2 = 'LMNPQRSTUV';
const at = () => new Date().toISOString();

(async () => {
  const env = await initializeTestEnvironment({
    projectId: 'demo-majasco',
    database: { rules: fs.readFileSync(path.join(__dirname, '..', 'database.rules.json'), 'utf8'), host: '127.0.0.1', port: 9000 },
  });
  let n = 0, ng = 0;
  const t = async (name, p) => { n++; try { await p; console.log('OK  ', name); } catch (e) { ng++; console.log('NG  ', name, '-', (e && e.message || e).toString().slice(0, 120)); } };

  // 準備: A は LID の持ち主、B は別人。古いリスト OLD は持ち主なし（A のアカウントに付いている）
  await env.withSecurityRulesDisabled(async c => {
    const db = c.database();
    await db.ref('users/userA').set({ listId: LID });
    await db.ref('users/userB').set({ listId: LID2 });
    await db.ref('mylists/' + OLD).set({ id: OLD, createdAt: at(), groups: { [GID]: { at: at(), name: '古い試合' } } });
  });
  const A = env.authenticatedContext('userA').database();
  const B = env.authenticatedContext('userB').database();
  const U = env.unauthenticatedContext().database();

  // 作る
  await t('ログインしていない人は一覧を作れない', assertFails(U.ref('mylists/' + LID).set({ id: LID, createdAt: at() })));
  await t('持ち主なしでは作れない', assertFails(A.ref('mylists/' + LID).set({ id: LID, createdAt: at() })));
  await t('他人を持ち主にして作れない', assertFails(A.ref('mylists/' + LID).set({ id: LID, owner: 'userB', createdAt: at() })));
  await t('自分を持ち主にして作れる', assertSucceeds(A.ref('mylists/' + LID).set({ id: LID, owner: 'userA', createdAt: at(), groups: { [GID]: { at: at(), name: '最初の試合' } } })));
  await t('もうある一覧は作り直せない（丸ごと上書き）', assertFails(A.ref('mylists/' + LID).set({ id: LID, owner: 'userA', createdAt: at() })));

  // 読む
  await t('一覧は読める（IDを知っている人）', assertSucceeds(U.ref('mylists/' + LID).once('value')));

  // 足す・直す
  await t('持ち主は試合を足せる', assertSucceeds(A.ref(`mylists/${LID}/groups/${GID2}`).update({ at: at(), name: '二つめ', deleted: null })));
  await t('持ち主はまとめて足せる（複数の場所の更新）', assertSucceeds(A.ref('mylists/' + LID).update({ ['groups/ABCDEFGHJM']: { at: at(), name: 'まとめて' } })));
  await t('持ち主は分類を付けられる', assertSucceeds(A.ref(`mylists/${LID}/groups/${GID}`).update({ role: 'play', me: 2 })));
  await t('持ち主は名前を変えられる', assertSucceeds(A.ref(`mylists/${LID}/groups/${GID}`).update({ name: '名前を変えた' })));
  await t('別人は試合を足せない', assertFails(B.ref(`mylists/${LID}/groups/ZZZZZZZZZZ`).update({ at: at(), name: 'x' })));
  await t('ログインしていない人は試合を足せない', assertFails(U.ref(`mylists/${LID}/groups/ZZZZZZZZZZ`).update({ at: at(), name: 'x' })));
  await t('別人は名前を変えられない', assertFails(B.ref(`mylists/${LID}/groups/${GID}`).update({ name: 'いたずら' })));

  // 消す
  await t('持ち主は削除の印を付けられる', assertSucceeds(A.ref(`mylists/${LID}/groups/${GID2}`).update({ deleted: true })));
  await t('持ち主は削除の印を外せる', assertSucceeds(A.ref(`mylists/${LID}/groups/${GID2}`).update({ at: at(), deleted: null })));
  await t('別人は削除の印を付けられない', assertFails(B.ref(`mylists/${LID}/groups/${GID2}`).update({ deleted: true })));
  await t('持ち主でも試合の項目そのものは消せない', assertFails(A.ref(`mylists/${LID}/groups/${GID}`).remove()));
  await t('持ち主でも試合の一覧（groups）は消せない', assertFails(A.ref(`mylists/${LID}/groups`).remove()));
  await t('持ち主でも一覧ごとは消せない', assertFails(A.ref('mylists/' + LID).remove()));
  await t('別人は一覧ごと消せない', assertFails(B.ref('mylists/' + LID).remove()));
  await t('ログインしていない人は一覧ごと消せない', assertFails(U.ref('mylists/' + LID).remove()));
  await t('groups を丸ごと置き換えられない', assertFails(A.ref(`mylists/${LID}/groups`).set({ [GID]: { at: at() } })));
  await t('持ち主を変えられない（本人でも）', assertFails(A.ref(`mylists/${LID}/owner`).set('userB')));
  await t('別人は持ち主を自分にできない', assertFails(B.ref(`mylists/${LID}/owner`).set('userB')));

  // 持ち主の無い古いリスト
  await t('古いリストには持ち主が付くまで書けない', assertFails(A.ref(`mylists/${OLD}/groups/${GID2}`).update({ at: at() })));
  await t('自分のアカウントに付いていないリストは持ち主になれない', assertFails(A.ref(`mylists/${OLD}/owner`).set('userA')));
  await env.withSecurityRulesDisabled(c => c.database().ref('users/userA/listId').set(OLD));
  await t('別人は古いリストの持ち主になれない', assertFails(B.ref(`mylists/${OLD}/owner`).set('userB')));
  await t('アカウントに付いた古いリストは本人が持ち主になれる', assertSucceeds(A.ref(`mylists/${OLD}/owner`).set('userA')));
  await t('持ち主になったら試合を足せる', assertSucceeds(A.ref(`mylists/${OLD}/groups/${GID2}`).update({ at: at(), name: '足した' })));
  await t('古い試合の項目もそのまま残っている', env.withSecurityRulesDisabled(async c => {
    const v = (await c.database().ref(`mylists/${OLD}/groups/${GID}/name`).once('value')).val();
    if (v !== '古い試合') throw new Error('消えている: ' + v);
  }));

  // 形のチェック（前と同じ）
  await t('おかしな試合IDは足せない', assertFails(A.ref(`mylists/${OLD}/groups/bad`).update({ at: at() })));
  await t('知らない項目は書けない', assertFails(A.ref(`mylists/${OLD}/groups/${GID}`).update({ foo: 1 })));
  await t('一覧の直下に知らない項目は書けない', assertFails(A.ref(`mylists/${OLD}/foo`).set(1)));

  // マイページの名前（users/{uid}/myName・本人だけ）とアイコン（avatars/{uid}・すべての牌から選べる）。2026-10-27
  await t('自分の名前を保存できる', assertSucceeds(A.ref('users/userA/myName').set('むにぃ')));
  await t('名前を消せる（自動の名前に戻す）', assertSucceeds(A.ref('users/userA/myName').remove()));
  await t('空の名前は入れられない', assertFails(A.ref('users/userA/myName').set('')));
  await t('長すぎる名前は入れられない', assertFails(A.ref('users/userA/myName').set('あ'.repeat(17))));
  await t('他人の名前は書けない', assertFails(B.ref('users/userA/myName').set('いたずら')));
  await t('他人の名前は読めない', assertFails(B.ref('users/userA/myName').once('value')));
  for (const k of ['m9', 'p5r', 's7', 'z2', 'z5', 'f8', 'ini', 'dice', 'chicha-ura', 'yakitori-ura', 'tb100', 'tb10000', 'tb100x5', 'ct500', 'cttobi', 'd1', 'd6', 'chip-r', 'chip-k', 'haiyose', 'back', 'taku', 'taku-top', 'sidetable', 'oshibori', 'oolong'])
    await t(`アイコンに ${k} を選べる`, assertSucceeds(A.ref('avatars/userA').set({ k, c: '#177083' })));
  for (const k of ['m0', 'm10', 'z8', 'f9', 'x1', 'evil', 'd5', 'd7', 'chip-x', 'tb1000', 'ct200', 'chicha-omote'])
    await t(`決まっていない絵 ${k} は選べない`, assertFails(A.ref('avatars/userA').set({ k, c: '#177083' })));
  await t('他人のアイコンは書けない', assertFails(B.ref('avatars/userA').set({ k: 'm1', c: '#177083' })));
  await t('アイコンはだれでも読める', assertSucceeds(U.ref('avatars/userA').once('value')));

  console.log(`\n${n - ng}/${n} ${ng ? 'FAILED' : 'ALL PASS'}`);
  await env.cleanup();
  process.exit(ng ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
