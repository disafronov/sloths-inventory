## [1.4.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v1.3.0...v1.4.0-rc.1) (2026-05-02)

### Features

* enhance application group management with post-migrate enforcement ([b9835a6](https://github.com/disafronov/sloths-inventory/commit/b9835a6ed4b43d5d7d7334daa0a3fa06460119fa))
* implement application-defined auth groups and permissions enforcement ([1cb6225](https://github.com/disafronov/sloths-inventory/commit/1cb6225dd04ae313b3d2b2751ff0b3f17e96e975))
* implement view-only user restrictions in admin interface ([50a3a98](https://github.com/disafronov/sloths-inventory/commit/50a3a98243e5b58ca953b274eaec508fd138b07e))

## [1.3.0](https://github.com/disafronov/sloths-inventory/compare/v1.2.0...v1.3.0) (2026-05-02)

### Features

* add functionality to filter pending transfer offers in UI ([9b7db80](https://github.com/disafronov/sloths-inventory/commit/9b7db80223a0db1822c4383f889b82c5f6922872))
* add translations for password change and inventory item edits ([3be5a0c](https://github.com/disafronov/sloths-inventory/commit/3be5a0c660494566fa9d70b9101966941d4fe4cd))
* add user password change functionality ([966c074](https://github.com/disafronov/sloths-inventory/commit/966c074ea207ca600812b1c67720d4696519636e))
* auto-accept pending transfers for receivers without linked users ([c283452](https://github.com/disafronov/sloths-inventory/commit/c2834520fc25918004d3c9f5907d375e2e7b1f42))
* enhance operation editing restrictions in admin interface ([ced73da](https://github.com/disafronov/sloths-inventory/commit/ced73dad6a6618718df8dd47af9d463977b2cece))
* enhance password change view for non-staff users ([3f4bdf8](https://github.com/disafronov/sloths-inventory/commit/3f4bdf83467cd60fdfa8351d06f52de96d7e73b7))
* enhance transfer creation flow for existing pending transfers ([f357b38](https://github.com/disafronov/sloths-inventory/commit/f357b389d3d247ff5dd4c29e55cadbe4c55fccad))
* implement catalog correction window for time-bounded edits ([ee5c909](https://github.com/disafronov/sloths-inventory/commit/ee5c90944d737b9e4017d1421d1d0fc30b40d9a4))
* implement time-bound editing restrictions for item master data ([4febab4](https://github.com/disafronov/sloths-inventory/commit/4febab43da444d1bfa598352940248cc9550e760))
* implement update_offer method for PendingTransfer ([e032367](https://github.com/disafronov/sloths-inventory/commit/e0323674db18f8cc6b36d6d346afd38808c9057f))
* refine item editing permissions based on operation history ([5d3ca8c](https://github.com/disafronov/sloths-inventory/commit/5d3ca8c3bd59acb73aea80ae05261c81c30ea1c1))

### Bug Fixes

* handle validation errors in transfer creation ([eeb4c24](https://github.com/disafronov/sloths-inventory/commit/eeb4c24497cb13443ce44cf798b0f3f965a1796c))

## [1.3.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v1.3.0-rc.1...v1.3.0-rc.2) (2026-05-02)

### Features

* add functionality to filter pending transfer offers in UI ([d51897a](https://github.com/disafronov/sloths-inventory/commit/d51897a82b46766c2628136729f9ec616e6ff506))
* auto-accept pending transfers for receivers without linked users ([b4a7b4e](https://github.com/disafronov/sloths-inventory/commit/b4a7b4e4d6c2621dba079b56656b06ab93b19b11))
* enhance operation editing restrictions in admin interface ([0b299d8](https://github.com/disafronov/sloths-inventory/commit/0b299d8c9eea11ce0bab5bd00441ecafd6ecfa91))
* implement catalog correction window for time-bounded edits ([1d46cea](https://github.com/disafronov/sloths-inventory/commit/1d46cea4a5deca8adb137c3fc4febcc3f00a4cdd))
* implement time-bound editing restrictions for item master data ([a724da0](https://github.com/disafronov/sloths-inventory/commit/a724da076796006ec7a8b0663e9934dda5f02ecd))
* refine item editing permissions based on operation history ([684a761](https://github.com/disafronov/sloths-inventory/commit/684a7619a2e7f29adcf50409763213ec19357695))

### Bug Fixes

* handle validation errors in transfer creation ([1d28df2](https://github.com/disafronov/sloths-inventory/commit/1d28df230f752bdd03c5222196d4dfb4d3fc54e0))

## [1.3.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v1.2.0...v1.3.0-rc.1) (2026-05-01)

### Features

* add translations for password change and inventory item edits ([a7613c5](https://github.com/disafronov/sloths-inventory/commit/a7613c5312aaa58c6cdc0988fec9f4a1a0bce450))
* add user password change functionality ([325bd53](https://github.com/disafronov/sloths-inventory/commit/325bd53e5f6947b2d1c88680663ef3919c2aeced))
* enhance password change view for non-staff users ([f2a3eaf](https://github.com/disafronov/sloths-inventory/commit/f2a3eafb1f73c621f7253f4a8b27c1c8a0050e6d))
* enhance transfer creation flow for existing pending transfers ([276aad9](https://github.com/disafronov/sloths-inventory/commit/276aad9831f10ac1d88843863ea0b5f4943ed3d8))
* implement update_offer method for PendingTransfer ([3d65779](https://github.com/disafronov/sloths-inventory/commit/3d65779b0184cb12047cf331f1b8c78fdf53f9cc))

## [1.2.0](https://github.com/disafronov/sloths-inventory/compare/v1.1.0...v1.2.0) (2026-05-01)

### Features

* add "Hand over" translation for improved clarity in item history ([92c4d35](https://github.com/disafronov/sloths-inventory/commit/92c4d35dd7c57a675d822984016d2c3a2e19c74f))
* add cancel method to PendingTransfer for improved transfer management ([84c04a6](https://github.com/disafronov/sloths-inventory/commit/84c04a6a454f4f6a8c48e91741e4b8f73226fe27))
* add create_offer method to PendingTransfer for streamlined transfer offers ([b20aa3e](https://github.com/disafronov/sloths-inventory/commit/b20aa3e2ae44b65a3683a43cac4de1eb202daf2c))
* display pending transfer notes in item history template ([796c326](https://github.com/disafronov/sloths-inventory/commit/796c3267066e34953f92cc9635f9a4e4190af66e))
* implement automatic acceptance of transfers for users without linked accounts ([31d731b](https://github.com/disafronov/sloths-inventory/commit/31d731b8f245cccdebdc9bb639af0b8cc4cc1c60))
* implement change location functionality for inventory items ([06e4118](https://github.com/disafronov/sloths-inventory/commit/06e4118ed634b0baf9d6feba3ada0ca6f26fae21))
* prefill expiration date for PendingTransfer in admin add form ([7ec08fa](https://github.com/disafronov/sloths-inventory/commit/7ec08fad745b3e6e195bdfcf07bfa0f925fe2fc5))
* prefill from_responsible field in PendingTransferAdmin based on item selection ([6a2f154](https://github.com/disafronov/sloths-inventory/commit/6a2f1546f0eaeacbcd83addf4aede7bd4bd5d3db))
* update button labels for change location and transfer forms ([8e33559](https://github.com/disafronov/sloths-inventory/commit/8e33559d2305023d2a039abca6ed5cf6fec4ada9))
* update PendingTransferAdmin to include readonly fields for transfer timestamps ([5f095a9](https://github.com/disafronov/sloths-inventory/commit/5f095a93f3fe466770107c51afe72915c39ac95f))

### Bug Fixes

* remove outdated button labels from translation files ([717de39](https://github.com/disafronov/sloths-inventory/commit/717de395d017ec128d569c517fd698bdeb297faf))
* update offer expiration message in translations ([2022f1c](https://github.com/disafronov/sloths-inventory/commit/2022f1c54497d2d5c75e3fdae134ee5da1b9b3ca))
* update Russian translation for offer expiration message ([f83df59](https://github.com/disafronov/sloths-inventory/commit/f83df59412c785f3fef3dad599629d364817672b))

## [1.2.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v1.2.0-rc.1...v1.2.0-rc.2) (2026-05-01)

### Bug Fixes

* update offer expiration message in translations ([6208250](https://github.com/disafronov/sloths-inventory/commit/6208250e7ad4522e763e273a54cc8bdbc15d780e))

## [1.2.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v1.1.0...v1.2.0-rc.1) (2026-05-01)

### Features

* add "Hand over" translation for improved clarity in item history ([36234e7](https://github.com/disafronov/sloths-inventory/commit/36234e79891e03e5a89d14c15ae4e0512eaa580d))
* add cancel method to PendingTransfer for improved transfer management ([13d32fa](https://github.com/disafronov/sloths-inventory/commit/13d32fa70cb74b15ab18f867c023ac0e49bc468e))
* add create_offer method to PendingTransfer for streamlined transfer offers ([105789d](https://github.com/disafronov/sloths-inventory/commit/105789d95dc85b1236de8c478df8db50c1d65b2b))
* display pending transfer notes in item history template ([05d2d90](https://github.com/disafronov/sloths-inventory/commit/05d2d90d48fbae05b3c99f5eb056e22de7d520a7))
* implement automatic acceptance of transfers for users without linked accounts ([3aaefec](https://github.com/disafronov/sloths-inventory/commit/3aaefecbd11bf7734e009e24ffea92b097a9f276))
* implement change location functionality for inventory items ([c277ef0](https://github.com/disafronov/sloths-inventory/commit/c277ef06baff8d5c1b8033be6d2161d0d6b438ca))
* prefill expiration date for PendingTransfer in admin add form ([8334a80](https://github.com/disafronov/sloths-inventory/commit/8334a809ff39a57c3f8f1ad3648f8b8f37b63287))
* prefill from_responsible field in PendingTransferAdmin based on item selection ([7cfb7df](https://github.com/disafronov/sloths-inventory/commit/7cfb7df9e5630ad6c49e3172bdea13ae56a077ec))
* update button labels for change location and transfer forms ([7cb8ac1](https://github.com/disafronov/sloths-inventory/commit/7cb8ac1f6e78b8ce9c8ae67b86685be1b27850ff))
* update PendingTransferAdmin to include readonly fields for transfer timestamps ([78a0383](https://github.com/disafronov/sloths-inventory/commit/78a03838a9c07fb18f2fa10482b351e8f2d8c469))

### Bug Fixes

* remove outdated button labels from translation files ([3ed95d2](https://github.com/disafronov/sloths-inventory/commit/3ed95d2a107fce86dbb059a24e6ea6eedf46a83d))
* update Russian translation for offer expiration message ([0b38a8c](https://github.com/disafronov/sloths-inventory/commit/0b38a8c271ab6058853a9b81dae640994c0ec6c5))

## [1.1.0](https://github.com/disafronov/sloths-inventory/compare/v1.0.0...v1.1.0) (2026-05-01)

### Features

* add "Transfer" terminology and translations for improved clarity ([fc234cb](https://github.com/disafronov/sloths-inventory/commit/fc234cb1f1116a22099ba2f36134aef8800dd8c1))
* add change location functionality for inventory items ([2bc8903](https://github.com/disafronov/sloths-inventory/commit/2bc8903894509ce943410c4187b0383b2c176b71))
* add inventory pending transfer expiration setting ([ef51b4b](https://github.com/disafronov/sloths-inventory/commit/ef51b4be8b05f9572166d400aaf6aa089a2bb2e3))
* add new translation for "View item" in English and Russian ([ab523a6](https://github.com/disafronov/sloths-inventory/commit/ab523a626639cdd1dbd08cf9a6b28bc3637b2f3d))
* add notes field to change location functionality ([9419879](https://github.com/disafronov/sloths-inventory/commit/9419879709664277bfe556d2073decc7c18a0551))
* add optional details fields for location and transfer creation ([c872a8f](https://github.com/disafronov/sloths-inventory/commit/c872a8f5bc0de986ea4ae9ef15c967dcfbded3e8))
* add searchable select component for location filtering ([623564a](https://github.com/disafronov/sloths-inventory/commit/623564a160d5a8f74d2fca6fe320ab24b50ffa49))
* add user identity display in user menu ([72756f0](https://github.com/disafronov/sloths-inventory/commit/72756f0d3f9ddeb2b3219306e423493f039598d0))
* allow both sender and receiver to cancel transfers ([c2cfdee](https://github.com/disafronov/sloths-inventory/commit/c2cfdee6ef97ef1ad0d9b1ef852509cd632462b7))
* display current location in change location form ([b8e99a3](https://github.com/disafronov/sloths-inventory/commit/b8e99a35cb656520bdead30155b06a16744fe3e4))
* enhance "My items" functionality with filtering options ([df9dd16](https://github.com/disafronov/sloths-inventory/commit/df9dd1682455372a9db2c896a5e850d5b3b97a22))
* enhance form action styling for improved layout consistency ([c5994d2](https://github.com/disafronov/sloths-inventory/commit/c5994d22abed632319629c605620d34ba0b64b4a))
* enhance item card and history layout with new styles and structure ([9fb3e4a](https://github.com/disafronov/sloths-inventory/commit/9fb3e4aa238ee151573a8d2a6844e30af4b3b82c))
* enhance item card display and structure ([5d846e4](https://github.com/disafronov/sloths-inventory/commit/5d846e42f57cd26a116213d51a6b1bf13016e017))
* enhance item history view to support pending transfers ([fdcda84](https://github.com/disafronov/sloths-inventory/commit/fdcda8436444888cb079e1fd61f320577ea0171a))
* enhance item transfer functionality and coverage ([8e2f223](https://github.com/disafronov/sloths-inventory/commit/8e2f223cfcc6e3086faf5ee2ab54ab56d8abafdf))
* enhance model ordering and admin autocomplete fields ([a549477](https://github.com/disafronov/sloths-inventory/commit/a549477982173a994d95540e9a7494c46fa6c26d))
* enhance previous items view with transfer details ([ce03522](https://github.com/disafronov/sloths-inventory/commit/ce03522cdc609095340b1663843de94d6ad5ebb6))
* enhance transfer and inventory templates with new translations and structure ([bd11087](https://github.com/disafronov/sloths-inventory/commit/bd110873b00ea37c318c1209499dd2d4dca58847))
* enhance transfer card layout and styling for improved usability ([505d2e9](https://github.com/disafronov/sloths-inventory/commit/505d2e9a986ad94909bcde4a3cf3a3e241fa3c64))
* enhance transfer creation form with searchable select ([5c11c7b](https://github.com/disafronov/sloths-inventory/commit/5c11c7b8c332aa2e50db2ffeba68965c6297bf31))
* enhance transfer creation with improved error handling and UI updates ([67f2ed7](https://github.com/disafronov/sloths-inventory/commit/67f2ed721fb1264f94eaf280ebbf657fc0e8393f))
* enhance transfer creation with notes field and form styling ([6745fd9](https://github.com/disafronov/sloths-inventory/commit/6745fd9042e96d89c0dea3acf01d683f895d662f))
* enhance transfer expiry display in UI ([9428f29](https://github.com/disafronov/sloths-inventory/commit/9428f291a9b4c0022900eddd36393d4590899175))
* implement dynamic gradient for transfer cards based on deadline ([2939830](https://github.com/disafronov/sloths-inventory/commit/293983045a4c5f3a06eb173777200fe678477396))
* implement pending item transfer functionality ([fcf5d50](https://github.com/disafronov/sloths-inventory/commit/fcf5d50775d664a156014df2a4e558600182109b))
* implement search functionality for inventory items ([c9575d7](https://github.com/disafronov/sloths-inventory/commit/c9575d760e88a5dbed0449ed2b950e2a7bde0ac5))
* implement spacing scale for consistent vertical rhythm in app.css ([02db1e0](https://github.com/disafronov/sloths-inventory/commit/02db1e0899a25cca8ac206cbd8c6ae56ba9a7d4f))
* improve change location functionality with error handling and UI updates ([b695fca](https://github.com/disafronov/sloths-inventory/commit/b695fca8858fe0a9663b6d643416771a68231df8))
* improve inline action layout for item history and transfers ([204588f](https://github.com/disafronov/sloths-inventory/commit/204588fe4ab62394c6954072ceb0dbf0cc262271))
* introduce item header card for consistent item detail display ([7fb3b37](https://github.com/disafronov/sloths-inventory/commit/7fb3b370d9544b78cbeaada44ddfd203b32ae1e1))
* prevent item duplication in my items view for active transfers ([c8bbaf6](https://github.com/disafronov/sloths-inventory/commit/c8bbaf61e3afdb8cf0958ee88740a3612334cd9a))
* refactor transfer handling and UI components ([9106c0f](https://github.com/disafronov/sloths-inventory/commit/9106c0fb369e0dc1fbda624430cd6edcca2e483e))
* restructure transfer card and expiry display for improved clarity ([4ff7f08](https://github.com/disafronov/sloths-inventory/commit/4ff7f0820c21767c418f305a4684fbc53fc04d80))
* update form styling and structure for improved usability ([d2922a4](https://github.com/disafronov/sloths-inventory/commit/d2922a4f0d8a1f4b3380860dc8fc8a96cb675c4c))
* update transfer offer expiration settings and UI ([11ef12e](https://github.com/disafronov/sloths-inventory/commit/11ef12ec01f9d8344db81295ba2ba76f8709e6ff))
* update transfer plaque styles for improved visual consistency ([38977c1](https://github.com/disafronov/sloths-inventory/commit/38977c12ee69212085820fc9c8b093a73ba92592))
* update transfer terminology and translations in templates ([53d7950](https://github.com/disafronov/sloths-inventory/commit/53d7950402c547301df4330e922c1d1660f26c20))
* update translations for transfer and filtering features ([ab3f355](https://github.com/disafronov/sloths-inventory/commit/ab3f3557278d1ef3e7a65b4408bd06dee83666cd))
* update user menu with SVG icon and CSS enhancements ([4f0eb66](https://github.com/disafronov/sloths-inventory/commit/4f0eb667360ae421cc897e5676bab8ed50f0c452))

### Bug Fixes

* add error handling for unchanged location in change location view ([73807f1](https://github.com/disafronov/sloths-inventory/commit/73807f1cbe6dee27e80eb997711993dcb7c54ce1))
* correct placement of transfer expiration message in transfer creation template ([9ea9b53](https://github.com/disafronov/sloths-inventory/commit/9ea9b532e247851bafade96428b8c7a9ce3af57a))
* sort languages with English first ([5e1d255](https://github.com/disafronov/sloths-inventory/commit/5e1d255da658f25c6bd469fda24b32150ed7de37))
* update card padding and margins for improved layout consistency ([8271c11](https://github.com/disafronov/sloths-inventory/commit/8271c11b3f2fe0a966ba797fac9be281d065ef0f))
* update date format for last item interaction in previous items view ([e18eba8](https://github.com/disafronov/sloths-inventory/commit/e18eba8045c7a230079f443c4db61202f3f9aabf))
* update English and Russian translations for transfer-related messages ([c298e92](https://github.com/disafronov/sloths-inventory/commit/c298e92f3a7cae13f20d55b4cc7274b8ef2a3d65))
* update item history template for clarity ([5b80501](https://github.com/disafronov/sloths-inventory/commit/5b80501481b9b1404868262d8203368861e84222))
* update navigation button styles and enhance active state indication ([be6c1fe](https://github.com/disafronov/sloths-inventory/commit/be6c1fe4150a416355a031f968337049bb2133ff))
* update redirection and cancel link in change location view ([c840019](https://github.com/disafronov/sloths-inventory/commit/c8400199bfaa2db4db06c31632bd329b8d32615b))
* update Russian translations for inventory terminology ([361783c](https://github.com/disafronov/sloths-inventory/commit/361783c7ba983d693d8d8872d90788db03ef967f))
* update Russian translations for transfer status ([98583a2](https://github.com/disafronov/sloths-inventory/commit/98583a245a3c050e689a2ba6f6cd1c7dc7370876))
* update STATIC_URL in settings.py for correct static file handling ([50b0759](https://github.com/disafronov/sloths-inventory/commit/50b07593435b35b41af29ab00e93b30b82f78bc1))

## [1.1.0-rc.12](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.11...v1.1.0-rc.12) (2026-05-01)

### Features

* enhance form action styling for improved layout consistency ([c5994d2](https://github.com/disafronov/sloths-inventory/commit/c5994d22abed632319629c605620d34ba0b64b4a))
* update transfer plaque styles for improved visual consistency ([38977c1](https://github.com/disafronov/sloths-inventory/commit/38977c12ee69212085820fc9c8b093a73ba92592))

## [1.1.0-rc.11](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.10...v1.1.0-rc.11) (2026-05-01)

### Features

* introduce item header card for consistent item detail display ([7fb3b37](https://github.com/disafronov/sloths-inventory/commit/7fb3b370d9544b78cbeaada44ddfd203b32ae1e1))

## [1.1.0-rc.10](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.9...v1.1.0-rc.10) (2026-05-01)

### Features

* add notes field to change location functionality ([9419879](https://github.com/disafronov/sloths-inventory/commit/9419879709664277bfe556d2073decc7c18a0551))
* add optional details fields for location and transfer creation ([c872a8f](https://github.com/disafronov/sloths-inventory/commit/c872a8f5bc0de986ea4ae9ef15c967dcfbded3e8))
* display current location in change location form ([b8e99a3](https://github.com/disafronov/sloths-inventory/commit/b8e99a35cb656520bdead30155b06a16744fe3e4))
* enhance transfer creation with improved error handling and UI updates ([67f2ed7](https://github.com/disafronov/sloths-inventory/commit/67f2ed721fb1264f94eaf280ebbf657fc0e8393f))
* enhance transfer creation with notes field and form styling ([6745fd9](https://github.com/disafronov/sloths-inventory/commit/6745fd9042e96d89c0dea3acf01d683f895d662f))
* improve change location functionality with error handling and UI updates ([b695fca](https://github.com/disafronov/sloths-inventory/commit/b695fca8858fe0a9663b6d643416771a68231df8))
* update form styling and structure for improved usability ([d2922a4](https://github.com/disafronov/sloths-inventory/commit/d2922a4f0d8a1f4b3380860dc8fc8a96cb675c4c))

### Bug Fixes

* correct placement of transfer expiration message in transfer creation template ([9ea9b53](https://github.com/disafronov/sloths-inventory/commit/9ea9b532e247851bafade96428b8c7a9ce3af57a))

## [1.1.0-rc.9](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.8...v1.1.0-rc.9) (2026-05-01)

### Features

* add inventory pending transfer expiration setting ([ef51b4b](https://github.com/disafronov/sloths-inventory/commit/ef51b4be8b05f9572166d400aaf6aa089a2bb2e3))
* enhance previous items view with transfer details ([ce03522](https://github.com/disafronov/sloths-inventory/commit/ce03522cdc609095340b1663843de94d6ad5ebb6))
* enhance transfer card layout and styling for improved usability ([505d2e9](https://github.com/disafronov/sloths-inventory/commit/505d2e9a986ad94909bcde4a3cf3a3e241fa3c64))
* enhance transfer expiry display in UI ([9428f29](https://github.com/disafronov/sloths-inventory/commit/9428f291a9b4c0022900eddd36393d4590899175))
* implement dynamic gradient for transfer cards based on deadline ([2939830](https://github.com/disafronov/sloths-inventory/commit/293983045a4c5f3a06eb173777200fe678477396))
* restructure transfer card and expiry display for improved clarity ([4ff7f08](https://github.com/disafronov/sloths-inventory/commit/4ff7f0820c21767c418f305a4684fbc53fc04d80))
* update transfer offer expiration settings and UI ([11ef12e](https://github.com/disafronov/sloths-inventory/commit/11ef12ec01f9d8344db81295ba2ba76f8709e6ff))

### Bug Fixes

* update date format for last item interaction in previous items view ([e18eba8](https://github.com/disafronov/sloths-inventory/commit/e18eba8045c7a230079f443c4db61202f3f9aabf))

## [1.1.0-rc.8](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.7...v1.1.0-rc.8) (2026-05-01)

### Features

* add "Transfer" terminology and translations for improved clarity ([fc234cb](https://github.com/disafronov/sloths-inventory/commit/fc234cb1f1116a22099ba2f36134aef8800dd8c1))
* add new translation for "View item" in English and Russian ([ab523a6](https://github.com/disafronov/sloths-inventory/commit/ab523a626639cdd1dbd08cf9a6b28bc3637b2f3d))
* allow both sender and receiver to cancel transfers ([c2cfdee](https://github.com/disafronov/sloths-inventory/commit/c2cfdee6ef97ef1ad0d9b1ef852509cd632462b7))
* enhance "My items" functionality with filtering options ([df9dd16](https://github.com/disafronov/sloths-inventory/commit/df9dd1682455372a9db2c896a5e850d5b3b97a22))
* enhance item card and history layout with new styles and structure ([9fb3e4a](https://github.com/disafronov/sloths-inventory/commit/9fb3e4aa238ee151573a8d2a6844e30af4b3b82c))
* enhance item card display and structure ([5d846e4](https://github.com/disafronov/sloths-inventory/commit/5d846e42f57cd26a116213d51a6b1bf13016e017))
* enhance transfer and inventory templates with new translations and structure ([bd11087](https://github.com/disafronov/sloths-inventory/commit/bd110873b00ea37c318c1209499dd2d4dca58847))
* enhance transfer creation form with searchable select ([5c11c7b](https://github.com/disafronov/sloths-inventory/commit/5c11c7b8c332aa2e50db2ffeba68965c6297bf31))
* implement spacing scale for consistent vertical rhythm in app.css ([02db1e0](https://github.com/disafronov/sloths-inventory/commit/02db1e0899a25cca8ac206cbd8c6ae56ba9a7d4f))
* improve inline action layout for item history and transfers ([204588f](https://github.com/disafronov/sloths-inventory/commit/204588fe4ab62394c6954072ceb0dbf0cc262271))
* prevent item duplication in my items view for active transfers ([c8bbaf6](https://github.com/disafronov/sloths-inventory/commit/c8bbaf61e3afdb8cf0958ee88740a3612334cd9a))
* refactor transfer handling and UI components ([9106c0f](https://github.com/disafronov/sloths-inventory/commit/9106c0fb369e0dc1fbda624430cd6edcca2e483e))
* update transfer terminology and translations in templates ([53d7950](https://github.com/disafronov/sloths-inventory/commit/53d7950402c547301df4330e922c1d1660f26c20))
* update translations for transfer and filtering features ([ab3f355](https://github.com/disafronov/sloths-inventory/commit/ab3f3557278d1ef3e7a65b4408bd06dee83666cd))

### Bug Fixes

* add error handling for unchanged location in change location view ([73807f1](https://github.com/disafronov/sloths-inventory/commit/73807f1cbe6dee27e80eb997711993dcb7c54ce1))
* update card padding and margins for improved layout consistency ([8271c11](https://github.com/disafronov/sloths-inventory/commit/8271c11b3f2fe0a966ba797fac9be281d065ef0f))
* update English and Russian translations for transfer-related messages ([c298e92](https://github.com/disafronov/sloths-inventory/commit/c298e92f3a7cae13f20d55b4cc7274b8ef2a3d65))
* update redirection and cancel link in change location view ([c840019](https://github.com/disafronov/sloths-inventory/commit/c8400199bfaa2db4db06c31632bd329b8d32615b))
* update Russian translations for inventory terminology ([361783c](https://github.com/disafronov/sloths-inventory/commit/361783c7ba983d693d8d8872d90788db03ef967f))
* update Russian translations for transfer status ([98583a2](https://github.com/disafronov/sloths-inventory/commit/98583a245a3c050e689a2ba6f6cd1c7dc7370876))

## [1.1.0-rc.7](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.6...v1.1.0-rc.7) (2026-04-30)

### Features

* enhance item history view to support pending transfers ([fdcda84](https://github.com/disafronov/sloths-inventory/commit/fdcda8436444888cb079e1fd61f320577ea0171a))

## [1.1.0-rc.6](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.5...v1.1.0-rc.6) (2026-04-30)

### Features

* enhance item transfer functionality and coverage ([8e2f223](https://github.com/disafronov/sloths-inventory/commit/8e2f223cfcc6e3086faf5ee2ab54ab56d8abafdf))
* implement pending item transfer functionality ([fcf5d50](https://github.com/disafronov/sloths-inventory/commit/fcf5d50775d664a156014df2a4e558600182109b))

## [1.1.0-rc.5](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.4...v1.1.0-rc.5) (2026-04-30)

### Bug Fixes

* sort languages with English first ([5e1d255](https://github.com/disafronov/sloths-inventory/commit/5e1d255da658f25c6bd469fda24b32150ed7de37))

## [1.1.0-rc.4](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.3...v1.1.0-rc.4) (2026-04-30)

### Bug Fixes

* update navigation button styles and enhance active state indication ([be6c1fe](https://github.com/disafronov/sloths-inventory/commit/be6c1fe4150a416355a031f968337049bb2133ff))

## [1.1.0-rc.3](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.2...v1.1.0-rc.3) (2026-04-30)

### Features

* add user identity display in user menu ([72756f0](https://github.com/disafronov/sloths-inventory/commit/72756f0d3f9ddeb2b3219306e423493f039598d0))
* update user menu with SVG icon and CSS enhancements ([4f0eb66](https://github.com/disafronov/sloths-inventory/commit/4f0eb667360ae421cc897e5676bab8ed50f0c452))

### Bug Fixes

* update item history template for clarity ([5b80501](https://github.com/disafronov/sloths-inventory/commit/5b80501481b9b1404868262d8203368861e84222))

## [1.1.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v1.1.0-rc.1...v1.1.0-rc.2) (2026-04-30)

### Features

* add searchable select component for location filtering ([623564a](https://github.com/disafronov/sloths-inventory/commit/623564a160d5a8f74d2fca6fe320ab24b50ffa49))
* enhance model ordering and admin autocomplete fields ([a549477](https://github.com/disafronov/sloths-inventory/commit/a549477982173a994d95540e9a7494c46fa6c26d))
* implement search functionality for inventory items ([c9575d7](https://github.com/disafronov/sloths-inventory/commit/c9575d760e88a5dbed0449ed2b950e2a7bde0ac5))

## [1.1.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v1.0.0...v1.1.0-rc.1) (2026-04-30)

### Features

* add change location functionality for inventory items ([2bc8903](https://github.com/disafronov/sloths-inventory/commit/2bc8903894509ce943410c4187b0383b2c176b71))

### Bug Fixes

* update STATIC_URL in settings.py for correct static file handling ([50b0759](https://github.com/disafronov/sloths-inventory/commit/50b07593435b35b41af29ab00e93b30b82f78bc1))

## [1.0.0](https://github.com/disafronov/sloths-inventory/compare/v0.11.0...v1.0.0) (2026-04-30)

### ⚠ BREAKING CHANGES

* major release
* ready for major release

### Features

* **docker:** update Dockerfile for static file handling and server configuration ([456d840](https://github.com/disafronov/sloths-inventory/commit/456d8403290351ae310a8936c2c5b5e6c1c79e18))
* major release ([3b48520](https://github.com/disafronov/sloths-inventory/commit/3b4852088448aa0b7ad2c390d6b932b7e8155b23))
* ready for major release ([9aa9e7d](https://github.com/disafronov/sloths-inventory/commit/9aa9e7db855207ea5e281a8270e2666f9833dee2))
* **tests:** configure static file storage for pytest runs ([fd5aac1](https://github.com/disafronov/sloths-inventory/commit/fd5aac1db0e40a6e7d52024b75fcd5c949efc083))
* **tests:** enhance pytest configuration with tooling secret key ([ceffce3](https://github.com/disafronov/sloths-inventory/commit/ceffce35c147d3dc482426658b5a0c70797b3a9c))

### Bug Fixes

* **docker:** set SECRET_KEY for static file collection in Dockerfile ([bf06650](https://github.com/disafronov/sloths-inventory/commit/bf06650781f59fa7e49148082a3b3659a910976b))
* **settings:** disable debug mode for production ([91941b5](https://github.com/disafronov/sloths-inventory/commit/91941b51acb6ea03e770c670551428a99b13d94f))
* **settings:** make TIME_ZONE configurable via environment variable ([c35ed32](https://github.com/disafronov/sloths-inventory/commit/c35ed32b2791f6daf55e1e8abe69cd4f9f8916c3))

## [1.0.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.12.0-rc.1...v1.0.0-rc.1) (2026-04-30)

### ⚠ BREAKING CHANGES

* major release

### Features

* major release ([7b6d5f0](https://github.com/disafronov/sloths-inventory/commit/7b6d5f0df1800d0d8991af9a7a74377c553e6b65))

## [0.12.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.11.0...v0.12.0-rc.1) (2026-04-30)

### ⚠ BREAKING CHANGES

* ready for major release

### Features

* **docker:** update Dockerfile for static file handling and server configuration ([0f27b04](https://github.com/disafronov/sloths-inventory/commit/0f27b041e953e0d07df62edb446e080e74798965))
* ready for major release ([22ad2ac](https://github.com/disafronov/sloths-inventory/commit/22ad2ac5d839103e6a1f26ced43d8c851e604052))
* **tests:** configure static file storage for pytest runs ([d761b76](https://github.com/disafronov/sloths-inventory/commit/d761b768d85e1c7c311fe7cce6c2a9cdfc467a4f))
* **tests:** enhance pytest configuration with tooling secret key ([b3f8315](https://github.com/disafronov/sloths-inventory/commit/b3f83156e1cf0d5bb340255d64800d61001bf318))

### Bug Fixes

* **docker:** set SECRET_KEY for static file collection in Dockerfile ([19ae587](https://github.com/disafronov/sloths-inventory/commit/19ae587454d3647d643936b110ceda9aa89ab0df))
* **settings:** disable debug mode for production ([47fc36a](https://github.com/disafronov/sloths-inventory/commit/47fc36ac4f2ff725cffa640448bdfe8fbd9728b8))
* **settings:** make TIME_ZONE configurable via environment variable ([282c4b5](https://github.com/disafronov/sloths-inventory/commit/282c4b5d27df2b8c8ea053a55eeb9783e505be35))

## [0.11.0](https://github.com/disafronov/sloths-inventory/compare/v0.10.0...v0.11.0) (2026-04-30)

### Features

* add language selection option and improve UI styling ([33acf82](https://github.com/disafronov/sloths-inventory/commit/33acf82a3e72bc3aef9f3f3e65a6aa4aa62fa0f2))
* **nav:** implement mobile navigation with hamburger menu ([c6087ce](https://github.com/disafronov/sloths-inventory/commit/c6087ce604f164e76c92cb981f7678336700f569))

## [0.11.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v0.11.0-rc.1...v0.11.0-rc.2) (2026-04-29)

## [0.11.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.10.0...v0.11.0-rc.1) (2026-04-29)

### Features

* add language selection option and improve UI styling ([c5ea4b2](https://github.com/disafronov/sloths-inventory/commit/c5ea4b23c7f6018a1bcc7d2060caae06013f46be))
* **nav:** implement mobile navigation with hamburger menu ([e1b6629](https://github.com/disafronov/sloths-inventory/commit/e1b6629a0a8d31b35d8c5ff08bc21a9200b1e13e))

## [0.10.0](https://github.com/disafronov/sloths-inventory/compare/v0.9.0...v0.10.0) (2026-04-29)

### Features

* add "Previously my items" feature ([3dfa5ef](https://github.com/disafronov/sloths-inventory/commit/3dfa5ef9dd181404683c0cde63945bf8cf2d1258))
* add new links for "My items" and "Previously my items" in the base template ([0492bcc](https://github.com/disafronov/sloths-inventory/commit/0492bccc4e71fd9ce87d5c5171b24310ac68c608))
* enhance error messaging for operation edit restrictions ([1759af9](https://github.com/disafronov/sloths-inventory/commit/1759af989dec117bb649db20c8cdcdd8fa148970))
* enhance home view and URL structure ([e55c769](https://github.com/disafronov/sloths-inventory/commit/e55c7697736eea520983dd18de8dbde78ddbba69))
* implement edit time restriction for operations ([c1ab095](https://github.com/disafronov/sloths-inventory/commit/c1ab0955121ad6613ba01c3d131aca5d6c373fde))
* implement inventory management features ([1a23f19](https://github.com/disafronov/sloths-inventory/commit/1a23f19a13cf343b08fbc97abee6d462b5463f0a))
* make operation edit window configurable ([1d4b9f8](https://github.com/disafronov/sloths-inventory/commit/1d4b9f88c21ebddaa891b96a0375676456ce6744))

### Bug Fixes

* add error code for editing restriction in operations ([8887048](https://github.com/disafronov/sloths-inventory/commit/88870483047e913bb24dc5b0f2d625ad43d104b4))
* enforce handoff operation requirement in item history view ([6da7ede](https://github.com/disafronov/sloths-inventory/commit/6da7ede7d2c371d84500040a7f4318286e3fd827))
* update English translation for "Previously my items" ([abbabf3](https://github.com/disafronov/sloths-inventory/commit/abbabf366dcc677d61ab93cb9beddb82ad169988))
* update localization files and adjust message references ([10edb13](https://github.com/disafronov/sloths-inventory/commit/10edb13121950ae716f905b378b33fae6bc08452))
* update localization files and remove unused links in "My items" template ([aba9a09](https://github.com/disafronov/sloths-inventory/commit/aba9a093b3cebba3b4d888413c141512dff64661))
* update Russian localization for account linking message ([6fde91a](https://github.com/disafronov/sloths-inventory/commit/6fde91ad84c5e4795db247b8387a508262bd7702))
* update Russian translation for "Previously my items" ([0513707](https://github.com/disafronov/sloths-inventory/commit/05137071dcff80b16e45452c6ad1a0bfeffea9c2))

## [0.10.0-rc.5](https://github.com/disafronov/sloths-inventory/compare/v0.10.0-rc.4...v0.10.0-rc.5) (2026-04-29)

### Features

* enhance error messaging for operation edit restrictions ([22a280d](https://github.com/disafronov/sloths-inventory/commit/22a280d041641bc4e14e7383fabdf0ec7f122c66))
* implement edit time restriction for operations ([7ecc89f](https://github.com/disafronov/sloths-inventory/commit/7ecc89f3c1c07e4d86db9e79b7bb44aab72c642a))
* make operation edit window configurable ([6c73d20](https://github.com/disafronov/sloths-inventory/commit/6c73d20e1873ad7d9a36d87788ab983a786e5e94))

### Bug Fixes

* add error code for editing restriction in operations ([aa4b77a](https://github.com/disafronov/sloths-inventory/commit/aa4b77ab28d576f8738e80ad49c75a3deb1d0870))

## [0.10.0-rc.4](https://github.com/disafronov/sloths-inventory/compare/v0.10.0-rc.3...v0.10.0-rc.4) (2026-04-29)

### Bug Fixes

* update English translation for "Previously my items" ([21feacc](https://github.com/disafronov/sloths-inventory/commit/21feacceac507e62ebf27b532bb1cae584078a65))
* update Russian translation for "Previously my items" ([efdb7bc](https://github.com/disafronov/sloths-inventory/commit/efdb7bc53f08898d4ee07682de1e838e348291e7))

## [0.10.0-rc.3](https://github.com/disafronov/sloths-inventory/compare/v0.10.0-rc.2...v0.10.0-rc.3) (2026-04-29)

### Features

* add "Previously my items" feature ([8c86610](https://github.com/disafronov/sloths-inventory/commit/8c866109af281f533ca980ec9cbebf5d15a7605e))
* add new links for "My items" and "Previously my items" in the base template ([881d0c9](https://github.com/disafronov/sloths-inventory/commit/881d0c9c0630a08d8b717c546675953603ad01fd))

### Bug Fixes

* enforce handoff operation requirement in item history view ([76c3df1](https://github.com/disafronov/sloths-inventory/commit/76c3df1173184e9d431c4a56aa0a6565c2f95ce7))
* update localization files and adjust message references ([254cce4](https://github.com/disafronov/sloths-inventory/commit/254cce454968b28708f703fc4d9ed84230d8e2c3))
* update localization files and remove unused links in "My items" template ([2d6aa85](https://github.com/disafronov/sloths-inventory/commit/2d6aa85762ee976e97ed5ff604f9cac72cc05358))
* update Russian localization for account linking message ([46112c1](https://github.com/disafronov/sloths-inventory/commit/46112c12575f1aad3749337096772ba383702ca7))

## [0.10.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v0.10.0-rc.1...v0.10.0-rc.2) (2026-04-29)

### Features

* enhance home view and URL structure ([ddff8a9](https://github.com/disafronov/sloths-inventory/commit/ddff8a94be7bd431ce6cd8ea94d5c620bbd6570b))

## [0.10.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.9.0...v0.10.0-rc.1) (2026-04-29)

### Features

* implement inventory management features ([9b2ae60](https://github.com/disafronov/sloths-inventory/commit/9b2ae60baad23b14b440de8ffe53e7713ee45fbb))

## [0.9.0](https://github.com/disafronov/sloths-inventory/compare/v0.8.3...v0.9.0) (2026-04-29)

### Features

* add index to Operation model for improved query performance ([0b9d55d](https://github.com/disafronov/sloths-inventory/commit/0b9d55dca8ca3ce7c4ce3f5b5677b348fb39a0e0))
* add logging configuration to settings ([4e3b5d7](https://github.com/disafronov/sloths-inventory/commit/4e3b5d768713d3dbaee3038331e53aa3ea78bf8b))
* enforce append-only semantics for Operation model ([52d04cf](https://github.com/disafronov/sloths-inventory/commit/52d04cf2efb6b61ff85d32549a99ee9f5a5ddab9))
* implement permission checks for latest Operation in admin ([f0c8152](https://github.com/disafronov/sloths-inventory/commit/f0c8152b13d034e16d2d8ce7a4e950762c43e386))
* introduce common utilities and test configuration for Django project ([ce39309](https://github.com/disafronov/sloths-inventory/commit/ce39309c05769d5d27127f1715c43788f0e78d85))

### Bug Fixes

* enhance Dockerfile for internationalization support ([c302e80](https://github.com/disafronov/sloths-inventory/commit/c302e80863da045439c907793a6bab107b6f698c))
* enhance fieldset handling in BaseAdmin class ([673c454](https://github.com/disafronov/sloths-inventory/commit/673c454a881cd0fcfdfb44024e4a5e22a8b60ba3))
* enhance SECRET_KEY handling in settings ([73b774d](https://github.com/disafronov/sloths-inventory/commit/73b774d2507697b19e2f18b585e15c30412fe129))
* implement concurrency-safe updates in Operation model ([c1d04ff](https://github.com/disafronov/sloths-inventory/commit/c1d04fff3e99c51bbe2b08fb2381ceeff453b486))
* improve concurrency handling in Operation model ([dbbee3b](https://github.com/disafronov/sloths-inventory/commit/dbbee3bac0e675137a92ddb0a7967517cf63e9d1))
* improve database connection error handling in health check ([d3f5b6b](https://github.com/disafronov/sloths-inventory/commit/d3f5b6baf80cd81c172c2bfea5e8205708e477f7))
* improve handling of None values in CurrentOperationValue ([d2dd253](https://github.com/disafronov/sloths-inventory/commit/d2dd25379188e619d6e8c2d4909ca633d97396ce))
* improve validation logic in Operation model ([ec1d7f9](https://github.com/disafronov/sloths-inventory/commit/ec1d7f9791d30754933d43b913a05aa888d46b99))
* optimize queryset and caching in admin views ([8b9e372](https://github.com/disafronov/sloths-inventory/commit/8b9e372ecd0da61f43ea8433abadc5a5444306f0))
* optimize queryset retrieval in admin views ([8162a85](https://github.com/disafronov/sloths-inventory/commit/8162a85c1fd0d8d0d2c972085c689c54f024bebb))
* Potential fix for pull request finding 'CodeQL / Information exposure through an exception' ([e9f6297](https://github.com/disafronov/sloths-inventory/commit/e9f62975a4829601ca22528b8ff594661a953332))
* refine current operation retrieval in Item model ([048c761](https://github.com/disafronov/sloths-inventory/commit/048c761373fc47c51094f90557d81195a91c6257))
* refine database error handling in health check ([b070033](https://github.com/disafronov/sloths-inventory/commit/b0700332b3aeca91642d046103ba09b9e8331397))
* remove USE_L10N setting from settings.py ([d782693](https://github.com/disafronov/sloths-inventory/commit/d782693da51c692ecfe1aa793f2fbcfbfdb4bcdf))
* update database engine in settings.py ([16cc366](https://github.com/disafronov/sloths-inventory/commit/16cc366369aae5a35820fa85a50a4432a18d1a3f))
* update DEBUG setting to use environment variable ([c799f39](https://github.com/disafronov/sloths-inventory/commit/c799f390cfbc3c362f14fec168055af1e02fc171))
* update Dockerfile for development environment configuration ([366551e](https://github.com/disafronov/sloths-inventory/commit/366551efd9421cec802320c1f4607899aca5ded7))
* update Dockerfile to set ownership for source files ([bdbe43d](https://github.com/disafronov/sloths-inventory/commit/bdbe43d343dcc30fb8f3bcbc9c304eb9eb758071))
* update entrypoint commands in Docker Compose configuration ([bcea8d2](https://github.com/disafronov/sloths-inventory/commit/bcea8d26d634d3600369371028b4febe551a6e41))
* update template directory path in settings ([8de0952](https://github.com/disafronov/sloths-inventory/commit/8de0952813bbec7334fbb3113eedc61163b22aa4))
* update translation function in admin.py ([ebbac5f](https://github.com/disafronov/sloths-inventory/commit/ebbac5f4a6cf8857567fceaa51ecdd12f7c22bd6))

## [0.9.0-rc.5](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.4...v0.9.0-rc.5) (2026-04-29)

### Bug Fixes

* update template directory path in settings ([54e8ce5](https://github.com/disafronov/sloths-inventory/commit/54e8ce5bd52073a662f43a191c3ac22936cf88e9))

## [0.9.0-rc.4](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.3...v0.9.0-rc.4) (2026-04-29)

### Features

* add logging configuration to settings ([d4915bf](https://github.com/disafronov/sloths-inventory/commit/d4915bf6d2469bc536165e3c01d09e8235488b7b))

## [0.9.0-rc.3](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.2...v0.9.0-rc.3) (2026-04-29)

### Features

* add index to Operation model for improved query performance ([46f2685](https://github.com/disafronov/sloths-inventory/commit/46f2685ce7c3fb32e800cc0af20ebaa95d1ba07f))
* enforce append-only semantics for Operation model ([982591f](https://github.com/disafronov/sloths-inventory/commit/982591ff1d65bc97e697de28914691093c5c21c3))
* implement permission checks for latest Operation in admin ([3f8ab2b](https://github.com/disafronov/sloths-inventory/commit/3f8ab2b0185866ce12593946714f47b454dda93f))

### Bug Fixes

* enhance Dockerfile for internationalization support ([f813b86](https://github.com/disafronov/sloths-inventory/commit/f813b860ff5ab2bdf6cb26a4ed3bcff0a2cd39d1))
* enhance fieldset handling in BaseAdmin class ([c8b134e](https://github.com/disafronov/sloths-inventory/commit/c8b134eb7be7abba1f3a255a6859b052ea95d2df))
* enhance SECRET_KEY handling in settings ([ef8fc9b](https://github.com/disafronov/sloths-inventory/commit/ef8fc9b3ad9d66b29b6e3cda25897b9c3b559724))
* implement concurrency-safe updates in Operation model ([ee5adfb](https://github.com/disafronov/sloths-inventory/commit/ee5adfb0e4dfee59b1bb5591df6c09fc7a784376))
* improve concurrency handling in Operation model ([cc75fa0](https://github.com/disafronov/sloths-inventory/commit/cc75fa0db31da92e792a6054cf2b22ef3a9f789e))
* improve database connection error handling in health check ([f2006c0](https://github.com/disafronov/sloths-inventory/commit/f2006c051840f1f86542cf90dbd2d87891e980a6))
* improve handling of None values in CurrentOperationValue ([82cbdc0](https://github.com/disafronov/sloths-inventory/commit/82cbdc0d04aaf15edf933deb0c84465313ab7654))
* improve validation logic in Operation model ([f38ccc1](https://github.com/disafronov/sloths-inventory/commit/f38ccc1aa9c3bf62ef4b2a0b74520d7e6fcb4b4a))
* optimize queryset and caching in admin views ([34cc468](https://github.com/disafronov/sloths-inventory/commit/34cc468e1dc82bb20d3f9d82630286cf8f6478b0))
* optimize queryset retrieval in admin views ([f2fc8da](https://github.com/disafronov/sloths-inventory/commit/f2fc8da90e636ab29573c391fb07e580d3077f7f))
* refine current operation retrieval in Item model ([ce2eedd](https://github.com/disafronov/sloths-inventory/commit/ce2eedd4e591219c3777ffc78bf8d2d468c32e44))
* refine database error handling in health check ([f6ae3e7](https://github.com/disafronov/sloths-inventory/commit/f6ae3e7d51bb3ab95828857208db70775e3ef22f))
* remove USE_L10N setting from settings.py ([2c0e9cd](https://github.com/disafronov/sloths-inventory/commit/2c0e9cdcb719964e1258b068a3e315f2f6c93f6c))
* update database engine in settings.py ([6ef3bff](https://github.com/disafronov/sloths-inventory/commit/6ef3bff9c6ae1fc0382646b6fdc7105de30e8e9b))
* update DEBUG setting to use environment variable ([84887f9](https://github.com/disafronov/sloths-inventory/commit/84887f93600709aeb8a6f7b8e090f9146533890a))
* update Dockerfile for development environment configuration ([50ce5c0](https://github.com/disafronov/sloths-inventory/commit/50ce5c02e604e1b15914e74cf8a0f11670ed070f))
* update Dockerfile to set ownership for source files ([940d626](https://github.com/disafronov/sloths-inventory/commit/940d6266acb51b1515ac1bdfd9ba090d8b3604f8))
* update translation function in admin.py ([5459b32](https://github.com/disafronov/sloths-inventory/commit/5459b321e1d06ab1f21da8b2dfe78c870386b5dd))

## [0.9.0-rc.2](https://github.com/disafronov/sloths-inventory/compare/v0.9.0-rc.1...v0.9.0-rc.2) (2026-04-29)

### Bug Fixes

* update entrypoint commands in Docker Compose configuration ([c2849e1](https://github.com/disafronov/sloths-inventory/commit/c2849e11b17679081f0ce517f087a96dd8dbc8bb))

## [0.9.0-rc.1](https://github.com/disafronov/sloths-inventory/compare/v0.8.3...v0.9.0-rc.1) (2026-04-29)

### Features

* introduce common utilities and test configuration for Django project ([3436fde](https://github.com/disafronov/sloths-inventory/commit/3436fdec50f446dd720153e11bfcf8d3a9af6023))

### Bug Fixes

* Potential fix for pull request finding 'CodeQL / Information exposure through an exception' ([85b977d](https://github.com/disafronov/sloths-inventory/commit/85b977d187cf9041917cd467d443d59a3a10220c))

# Changelog

All notable changes to this project will be documented in this file.

## [0.8.0] - 2025-05-18

### 🚀 Features

- Добавление поддержки интернационализации и обновление шаблонов
- Добавление миграций для обновления полей моделей в приложениях catalogs, devices и inventory
- Удаление файлов локализации для английского и русского языков
- Добавление поддержки интернационализации для моделей и локализации
- Добавление миграции для обновления опций моделей в приложении catalogs
- Обновление файлов локализации для поддержки интернационализации
- Обновление моделей для поддержки интернационализации и добавление файлов локализации
- Добавление миграций для обновления опций моделей в приложениях devices и inventory
- Обновление админки для поддержки интернационализации
- Обновление поддержки интернационализации в приложениях catalogs, devices и inventory

### 🚜 Refactor

- Удаление проверки локального запроса из функций liveness и readiness

## [0.7.0] - 2025-05-18

### 🚀 Features

- Добавление функционала управления устройствами с CRUD операциями и соответствующими шаблонами
- Добавление фабрики DeviceFactory и тестов для CRUD операций устройств
- Добавление проверки состояния приложения с помощью liveness и readiness проб
- Добавление маршрутов для проверки состояния приложения через liveness и readiness
- Замена шаблонов устройств на общий шаблон и обновление локализации
- Обновление шаблонов для управления устройствами с использованием нового общего шаблона
- Добавление функционала аутентификации с кастомными представлениями входа и выхода
- Добавление начальных миграций для приложений catalogs, devices и inventory
- Добавление тестового раннера для pytest и инициализация тестового пакета
- Добавление нового шаблона base.html
- Добавление проверки доступа к пробам liveness и readiness
- Добавление приложения health с пробами liveness и readiness
- Добавление базового админ-класса и обновление админки устройств
- Добавление полей поиска в админ-классы
- Обновление админ-класса DeviceAdmin для улучшения поиска
- Обновление админ-классов для моделей Location, Responsible и Status
- Обновление админ-класса ResponsibleAdmin для улучшения отображения
- Обновление админ-класса OperationAdmin для улучшения отображения
- Обновление админ-класса ItemAdmin для улучшения отображения
- Обновление админ-классов для улучшения структуры полей
- Обновление метода get_fieldsets в админ-классе ItemAdmin для улучшения структуры отображения
- Добавление метода _format_empty_value в базовый админ-класс для обработки пустых значений
- Добавление миксина CurrentFieldMixin в админ-класс ItemAdmin для улучшения отображения текущих полей
- Добавление миксина DeviceFieldsMixin в админ-классы ItemAdmin и OperationAdmin для улучшения поиска и фильтрации
- Добавление базовой структуры приложения с главной страницей и шаблонами
- Обновление маршрутов приложения и удаление шаблона base.html
- Обновление шаблона base.html для улучшения структуры и стилей
- Добавление маршрутов для входа и выхода, обновление шаблонов для улучшения навигации
- Удаление представлений и маршрутов для управления устройствами
- Обновление шаблонов для улучшения структуры и стилей
- Обновление маршрутов и шаблонов для улучшения пользовательского интерфейса

### 🐛 Bug Fixes

- Исправление импорта модели Device из приложения catalogs вместо текущего приложения
- CSRF_TRUSTED_ORIGINS

### 🚜 Refactor

- Объединение импортов моделей из приложений catalogs и devices
- Удаление модели Device и упрощение админ-панели
- Удаление тестов для приложений catalogs, devices, inventory и общего теста
- Rm generated tests
- Rm migrations
- Обновление конфигурации pytest для игнорирования определенных файлов
- Удаление шаблонов base.html и login.html
- Обновление шаблонов и маршрутов для устройств
- Обновление шаблона base.html для улучшения локализации и структуры
- Удаление неиспользуемого кода из приложения common

### 📚 Documentation

- Update changelog for v0.7.0

### 🧪 Testing

- Добавление тестов для проверки состояния приложения через liveness и readiness

## [0.6.4] - 2025-05-18

### 🐛 Bug Fixes

- Исправление зависимости в workflow тестов, замена 'test' на 'tests'

### 🚜 Refactor

- Улучшение тестов и удаление устаревших функций в manage.py, добавление новых тестов для конфигурации приложений и настроек Django
- Перевод тестов конфигурации приложений и настроек Django на русский язык
- Добавление приложения 'common' в тесты конфигурации Django

### 📚 Documentation

- Update changelog for v0.6.4

## [0.6.3] - 2025-05-18

### 🐛 Bug Fixes

- Rename

### 📚 Documentation

- Update changelog for v0.6.3

## [0.6.2] - 2025-05-18

### 🐛 Bug Fixes

- Rename
- Rename
- Test

### 📚 Documentation

- Update changelog for v0.6.2

### ⚙️ Miscellaneous Tasks

- Обновление условий зависимости jobs в docker-publish.yml для поддержки динамического определения необходимости тестирования при pull_request событиях
- Добавление нового workflow для тестирования в tests.yml и упрощение логики в docker-publish.yml
- Исправление ссылки на ветку в docker-publish.yml для корректного запуска тестов при pull_request событиях
- Удаление лишнего шага "Sideload tests" в docker-publish.yml для упрощения логики workflow
- Добавление нового workflow для тестирования pull_request событий с использованием PostgreSQL
- Обновление ключа кэширования в pr-tests.yml для учета uv.lock и удаление лишних параметров установки
- Изменение триггера для workflow docker-publish и добавление шага для его вызова из pr-tests.yml
- Добавление триггера workflow_call в docker-publish.yml и упрощение вызова из pr-tests.yml

## [0.6.1] - 2025-05-18

### 🐛 Bug Fixes

- Move postgres

### 📚 Documentation

- Update changelog for v0.6.1

### ⚙️ Miscellaneous Tasks

- Добавить тестирование PR с использованием uv
- Улучшить тестирование PR с использованием PostgreSQL
- Улучшить шаги тестирования PR в GitHub Actions
- New workflow
- Revert workflow
- Fix uv
- Fix cache path
- Cache
- Python
- Test cache
- Test frozen
- Test
- Test
- Объединение тестов в один workflow и удаление старого файла tests.yml
- Обновление условий выполнения jobs в docker-publish.yml для поддержки pull_request и push событий
- Добавление параметров кэширования в docker-publish.yml для улучшения производительности
- Обновление параметров кэширования в docker-publish.yml для использования glob-выражения
- Добавление кэширования зависимостей uv в docker-publish.yml для повышения производительности
- Удаление лишнего пробела и пустой строки в docker-publish.yml для улучшения читаемости

## [0.6.0] - 2025-05-18

### 🚀 Features

- Оптимизация кода + тесты

### 📚 Documentation

- Update changelog for v0.6.0

## [0.5.0] - 2025-05-04

### 🚀 Features

- Восстановить отображение поля location в админке OperationAdmin

### 📚 Documentation

- Update changelog for v0.5.0

## [0.4.0] - 2025-05-04

### 🚀 Features

- Обновить админку ItemAdmin для добавления поля serial_number в список ссылок
- Обновить админку ItemAdmin для добавления новых полей текущего статуса и ответственного

### 🐛 Bug Fixes

- Улучшить отображение текущего статуса, местоположения и ответственного в админке ItemAdmin

### 📚 Documentation

- Update changelog for v0.4.0

## [0.3.0] - 2025-05-04

### 🚀 Features

- Добавить приложение Inventory в настройки проекта
- Добавить приложение Inventory с базовой конфигурацией
- Обновить админку для модели Device и добавить модель Item
- Обновить админку для моделей Category, Manufacturer, Model, Type и Device
- Обновить админку модели Item для улучшения поиска
- Обновить поле серийного номера в модели Item
- Добавить модель Operation и обновить админку для Item
- Обновить админку модели Item для отображения текущих данных
- Улучшить админку модели Operation для отображения ответственного
- Улучшить отображение ответственного в админке модели Operation
- Добавить модель Responsible и обновить админку для управления ответственными
- Добавить модель Status и обновить админку для управления статусами
- Добавить метод get_full_name в админку модели Responsible и обновить порядок сортировки в модели Operation
- Добавить модели Category, Manufacturer, Model и Type, а также админку для управления ими
- Обновить модели и админку для управления устройствами и ответственными
- Добавить приложение devices в настройки проекта
- Обновить админку и модели для управления устройствами и статусами
- Восстановить и обновить модель Operation и админку для управления эксплуатацией
- Добавить тесты для моделей Category, Manufacturer, Model и Type
- Добавить тесты для моделей Item и Operation
- Добавить тесты для моделей Device, Location, Responsible и Status
- Добавить миграцию для моделей Category, Manufacturer, Model и Type
- Добавить начальную миграцию для моделей Location, Status, Responsible и Device
- Добавить начальную миграцию для моделей Item и Operation
- Заменить поле description на notes в моделях Category, Manufacturer, Model и Type
- Обновить админку и модели для использования поля notes вместо description
- Обновить админку и тесты для использования поля notes вместо description
- Обновить админку для классов Device, Location, Status, Category, Manufacturer, Model и Type
- Добавить автозаполнение для поля device в админке ItemAdmin
- Добавить поле notes в модель Responsible
- Обновить админку для классов Device, Location, Manufacturer, Model, Type, Item и Operation
- Добавить поле notes в миграции моделей Catalog, Device и Inventory

### 🐛 Bug Fixes

- Унифицировать форматирование полей в админке и моделях
- Унифицировать форматирование в классе DevicesConfig
- Унифицировать форматирование в моделях и тестах
- Заменить ValidationError на IntegrityError в тестах моделей Category, Manufacturer, Model и Type
- Заменить ValidationError на IntegrityError в тестах модели Device
- Обновить тесты модели Item и Operation для корректной обработки исключений

### 💼 Other

- Compose.yml rebuild

### 🚜 Refactor

- Обновить админку и модели для улучшения структуры и читаемости

### 📚 Documentation

- Update changelog for v0.3.0

### ⚙️ Miscellaneous Tasks

- Удалить неиспользуемый файл views.py
- Удалить неиспользуемый файл тестов

## [0.2.0] - 2025-05-03

### 🚀 Features

- Добавить базовую структуру приложения catalogs
- Добавить приложение catalogs в настройки Django
- Обновить настройки Docker Compose для Postgres
- Добавить сервис makemigrations в настройки Docker Compose
- Обновить настройки Docker Compose для проверки состояния сервиса Postgres
- Упростить настройки Docker Compose для сервиса Django, удалив ненужные комментарии и конфигурации
- Добавить модель Vendor и зарегистрировать её в админке Django
- Добавить модель Model и зарегистрировать её в админке Django
- Добавить модель Device и зарегистрировать её в админке Django
- Улучшить админку Django, добавив настройки для моделей Vendor, Model и Device
- Обновить админку Django, добавив ссылки для отображения и исправив порядок полей в моделях
- Изменить порядок отображения и фильтрации полей в админке для моделей Vendor, Model и Device
- Добавить модель Category и обновить админку для отображения и фильтрации устройств по категориям
- Изменить поле serial_number на catalog_number в модели Device и обновить админку для отображения и поиска по новому полю
- Изменить поведение полей в модели Device с CASCADE на PROTECT для обеспечения целостности данных
- Переименовать модель Vendor в Manufacturer и обновить соответствующие ссылки в админке и моделях
- Добавить автозаполнение для полей категории, производителя и модели в админке устройства
- Добавить уникальное ограничение для модели Device по полям category, manufacturer и model
- Добавить модель Type и обновить модель Device для использования нового поля
- Обновить модель Device и админку для улучшения отображения и поиска
- Изменить формат отображения модели Device для улучшения читаемости
- Добавить человекочитаемое имя для приложения Catalogs
- Добавить тесты для моделей Category, Manufacturer, Model, Type и Device

### 📚 Documentation

- Update changelog for v0.2.0

### ⚙️ Miscellaneous Tasks

- Disable docker build on main branch
- Compose

## [0.1.1] - 2025-04-11

### 🐛 Bug Fixes

- CSRF parenthesis

### 📚 Documentation

- Update changelog for v0.1.1

## [0.1.0] - 2025-04-11

### 🚀 Features

- CSRF_TRUSTED_ORIGINS

### 📚 Documentation

- Update changelog for v0.1.0

## [0.0.0] - 2025-04-09

### 🚀 Features

- Django
- Dockerfile (editable mode)
- Dockerfile MVP
- Compose.yml
- Env ALLOWED_HOSTS
- Compose sql loader
- Workflows

### 🐛 Bug Fixes

- --noreload

### 🚜 Refactor

- Dockerfile
- Dockerfile
- Pin base image
- Django entrypoint
- Remove makemigrations
- Docker stuff
- -> src
- Ignores
- Add postgres
- Paths and user
- Push on pr
- Remove .npmrc

### 📚 Documentation

- README.md

### ⚙️ Miscellaneous Tasks

- Gitignore
- .gitignore
- Ignores

<!-- generated by git-cliff -->
