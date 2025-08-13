import niquests
import asyncio
import os
import time
# import ua_generator

from sputchedtools import aio, enhance_loop, setup_logger, Anim, AnimChars, JSON
from datetime import datetime
from bs4 import BeautifulSoup
from git import Repo
# from typenodes import TypeNode

JSON = JSON()
log = setup_logger('up', clear_file=True)

CWD = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/') + '/'
urls_path = CWD + 'urls.txt'

github_latest_draft = 'https://api.github.com/repos/{}/{}/releases?per_page=5' # Owner, Repo Slug
urls_link = 'https://raw.githubusercontent.com/Sputchik/pdi/refs/heads/main/urls.txt'

github_map = {
	'7-Zip': ('ip7z', '7zip'),
	'ContextMenuManager': ('BluePointLilac', 'ContextMenuManager'),
	'Git': ('git-for-windows', 'git'),
	'OBS': ('obsproject', 'obs-studio'),
	'Rufus': ('pbatard', 'rufus'),
	'VCRedist 2005-2022': ('abbodi1406', 'vcredist'),
	'ZXP Installer': ('elements-storage', 'ZXPInstaller'),
	'Ungoogled Chromium': ('ungoogled-software', 'ungoogled-chromium-windows'),
	'DB Browser': ('sqlitebrowser', 'sqlitebrowser'),
	'OpenSSH': ('PowerShell', 'Win32-OpenSSH'),
	'LLVM': ('llvm', 'llvm-project'),
	'AyuGram': ('AyuGram', 'AyuGramDesktop'),
	'Git': ('git-for-windows', 'git'),
	'LibAvif': ('AOMediaCodec', 'libavif')

}

parse_map = {
	'RegistryFinder': 'https://registry-finder.com/',
	'Go': 'https://go.dev/dl/?mode=json',
	'Gradle': 'https://gradle.org/releases/',
	'Google_Earth_Pro': 'https://support.google.com/earth/answer/168344?hl=en#zippy=%2Cdownload-a-google-earth-pro-direct-installer',
	'Bluetooth': 'https://www.intel.com/content/www/us/en/download/18649/intel-wireless-bluetooth-drivers-for-windows-10-and-windows-11.html',
	'WiFi': 'https://www.intel.com/content/www/us/en/download/19351/intel-wireless-wi-fi-drivers-for-windows-10-and-windows-11.html',
	'Python': 'https://www.python.org/downloads/',
	'Node.js': 'https://nodejs.org/dist/index.json',
	'NVCleanstall': 'https://nvcleanstall.net/download',
	'K-Lite Codec': 'https://www.codecguide.com/download_k-lite_codec_pack_full.htm',
	'Everything': 'https://www.voidtools.com/',
	'qBitTorrent': 'https://www.qbittorrent.org/download',
	'Librewolf': 'https://gitlab.com/api/v4/projects/44042130/releases',
	'Blender': 'https://www.blender.org/download/',
	'OpenSSL': 'https://slproweb.com/download/win32_openssl_hashes.json',
	'Blender 3.3.X LTS': 'https://www.blender.org/download/lts/3-3/',
	'Blender 3.6.X LTS': 'https://www.blender.org/download/lts/3-6/',
	'WinSCP': 'https://winscp.net/eng/downloads.php',
	'ExifTool': 'https://exiftool.org/'

}

jetbrains_api = "https://data.services.jetbrains.com/products/releases"

jetbrains_progs = {
	'PyCharm': 'PCP',
	'IntelliJ IDEA': 'IIU',
}

jetbrains_params = {
	# "code": ['PCP', 'IIU', ],
	"latest": "true",
	"type": "release"
}

if not os.path.exists('token'):
	access_token = input('Github Access Token: ')
	open('token', 'w').write(access_token)

else:
	access_token = open('token', 'r').read().strip()

pdi_git = f"https://{access_token}@github.com/Sputchik/pdi.git"
os.chdir(CWD)
repo = Repo(CWD)
repo.remotes.origin.set_url(pdi_git)

github_headers = {
	'Authorization': f'Bearer {access_token}'
}
pdi_git = 'https://github.com/Sputchik/pdi.git'

# gtihub_node = TypeNode.create(None)

headers = {
	# 'User-Agent': ua_generator.generate('desktop', 'windows', 'firefox').text,
	'Cache-Control': 'no-cache',
	'Pragma': 'no-cache',
	'Accept-Language': 'en-US',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept': '*/*',
}

def sortify_batch_list(line: str):
	unpack = line.split('=', 1)
	if len(unpack) != 2: return line
	key, value = unpack

	value_list = value.split(';')
	if len(value_list) == 1:
		return line

	value_list = sorted(value_list, key = lambda x: (x[0].lower(), x[1:]))
	value = ';'.join(value_list)

	line = key + '=' + value
	return line

def get_line_index(lines, start_pattern):
	for index, line in enumerate(lines):
		if line.startswith(start_pattern):
			return index

def parse_categories(lines):
	cat_map = {}
	cat_index = get_line_index(lines, 'Categories=')
	categories = lines[cat_index].split('=')[1].split(';')

	cat_progs_start = get_line_index(lines, categories[0])
	cat_progs_end = get_line_index(lines, categories[-1]) + 1

	ext_start = cat_progs_end + 1
	ext_end = get_line_index(lines, 'url_') - 1

	for i in range(ext_start, ext_end):
		line = lines[i]
		lines[i] = sortify_batch_list(line)

	progs_lines = lines[cat_progs_start:cat_progs_end]

	for line in progs_lines:
		cat, progs = line.split('=')
		progs = sorted(progs.split(';'), key = lambda x: (x[0].lower(), x[1:]))
		cat_map[cat] = ';'.join(progs)

	return cat_map, '\n'.join(lines[ext_start:ext_end])

def progmap_to_txt(progmap):
	first_line = 'Categories=' + ';'.join(progmap['cats'].keys())
	cat_progs = '\n'.join([f"{key}={value}" for key, value in progmap['cats'].items()])
	urls = '\n'.join([f"url_{key.replace(' ', '_')}={value}" for key, value in progmap['urls'].items()])

	del progmap['cats']
	del progmap['urls']

	result = '\n\n'.join([first_line, cat_progs, *progmap.values(), urls])
	return result

async def parse_github_urls(session) -> dict:
	# data = await aio.open(cwd + 'urls.txt')
	data = await aio.get(urls_link, session = session, toreturn = 'text')
	if not data:
		log.warning(f'Failed to fetch urls.txt: {data}')

	lines: list[str] = data.splitlines()
	url_index = get_line_index(lines, 'url_')
	url_lines = lines[url_index:]

	cats, exts = parse_categories(lines)

	progmap = {
		'cats': cats,
		'exts': exts,
		'urls': dict(sorted({
			line.split('url_')[1].split('=')[0].replace('_', ' '): line.split('=', maxsplit = 1)[1] for line in url_lines
		}.items(), key = lambda x: (x[0].lower(), x[1:])))
	}

	# log.debug(f'Parsed prog map: {json.dumps(progmap, indent = 2)}')
	return progmap

def find_best_executable(versions: dict[str, str]) -> str:
	preferred_exe = None
	selected_exe = False
	preferred_msi = None
	fallback_zip = None

	for key in versions:
		lowered = key.lower()
		if 'arm' in lowered:
			log.debug(f'Armed: {lowered}')
			continue

		if key.endswith('.msi'):
			# Check if it's a preferred '64' version
			if '64' in key:
				preferred_msi = key
				break
			elif '32' in key and not preferred_msi:
				preferred_msi = key
			elif not preferred_msi:
				preferred_msi = key

		elif key.endswith('.exe'):
			# Check if it's a preferred '64' version
			if '64' in key and not selected_exe:
				preferred_exe = key
				selected_exe = True
			elif '32' in key and not preferred_exe:
				preferred_exe = key
			elif not preferred_exe:
				preferred_exe = key

		elif key.endswith('.zip'):
			if 'windows' in key:
				log.debug(f'ZIP Fallback: {key}')
				fallback_zip = key

	file_name = preferred_msi or preferred_exe or fallback_zip
	return versions.get(file_name)

async def direct_from_github(owner: str, project: str, session) -> str | None:
	url = github_latest_draft.format(owner, project)

	response = await aio.get(
		url,
		toreturn = 'json+status_code',
		session = session,
		headers = github_headers,
	)

	if not response:
		log.warning(f'Failed to fetch {project} latest version: {response}')
		return

	versions, status = response

	prefix = '✅' if status == 200 else '⚠️'
	print(f'{prefix} {status}: {project} - {url}')

	if status != 200 or not isinstance(versions, list):
		print(f'Fail: Github latest version for `{project}`: {url}')
		return

	url = None
	for version in versions:
		assets = version['assets']
		version_map = {unpack['name']: unpack['browser_download_url'] for unpack in assets}
		url = find_best_executable(version_map)

		if not url:
			continue

		log.debug(f'[{project}] Parsed best executable URL: {url}')
		break

	if url is None:
		input(f'[Fail]: {owner}-{project} Github version extraction')
		log.debug(f'[{project}] {versions}')

	return url

async def parse_prog(url = None, name = None, session = None, github = False, jetbrains = False):
	params = None

	if github:
		author, project = github_map[name]
		return (name, await direct_from_github(author, project, session))

	elif jetbrains:
		params = jetbrains_params.copy()
		params['code'] = url
		code = url
		url = jetbrains_api

	response = await aio.request('GET', url, toreturn = 'text+status_code', session = session, headers = headers, params = params)
	if not response:
		log.warning(f'Failed to fetch {name} url: {response}')
		return

	data, status = response

	prefix = '✅' if status == 200 else '⚠️'
	print(f'{prefix} {status}: {name} - {url}')
	if status != 200:
		log.debug(f'[{name}] {response}')
		return

	if jetbrains:
		try:
			response = JSON.parse(data)[code][0]
			download_url = response['downloads']['windows']['link']
			return name, download_url

		except (TypeError, KeyError):
			log.warning(f'[{name}] Failed to parse JetBrains download URL: {JSON.stringify(response, indent = 2)}')
			return

	if name == 'Go':
		version = JSON.parse(data)[0]['version'].split('go')[1]
		url = f'https://go.dev/dl/go{version}.windows-amd64.msi'
		return (name, url)

	elif name == 'Librewolf':
		latest = JSON.parse(data)[0]
		# Emulate github version map
		version_map = {k['name']: k['url'] for k in latest['assets']['links']}
		url = find_best_executable(version_map)
		return (name, url)

	soup = BeautifulSoup(data, 'lxml')

	if name == 'RegistryFinder':
		for a_tag in soup.find_all('a'):
			href = a_tag.get('href')
			if href and href.startswith('bin/'):
				url = f'https://registry-finder.com/{href}'
				break

	elif name == 'Google Earth Pro':
		lis = soup.find_all('li')

		for li in lis:
			if li.text and 'for Windows (64-bit)' in li.text:
				url = li.find('a').get('href')
				break

	elif name == 'Bluetooth' or name == 'WiFi':
		button = soup.find('button', {'data-wap_ref': 'download-button'})
		url = button.get('data-href')

	elif name == 'Gradle':
		div = soup.find('div', class_ = 'resources-contents')
		version = div.find('a').get('name')
		url = f'https://services.gradle.org/distributions/gradle-{version}-bin.zip'

	elif name == 'Python':
		a = soup.find('a', class_ = 'button')
		version = a.text.split(' ')[2]

		url = f'https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe'

	elif name == 'Node.js':
		data = JSON.parse(data)
		version = data[0]['version']
		url = f'https://nodejs.org/dist/{version}/node-{version}-x64.msi'

	elif name == 'NVCleanstall':
		a = soup.find('a', class_ = 'btn btn btn-info my-5')
		url = a.get('href')

	elif name == 'K-Lite Codec':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			if elem.text and elem.text == 'Server 2':
				url = elem.get('href')
				break

	elif name == 'Everything':
		a_elems = soup.find_all('a', class_ = 'button')

		for elem in a_elems:
			if elem.text and elem.text.endswith('64-bit'):
				url = 'https://voidtools.com'+ elem.get('href')
				break

	elif name == 'qBitTorrent':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			if elem.text and elem.text.startswith('Download qBittorrent '):
				version = elem.text.split(' ')[2].lstrip('v')
				url = f'https://netcologne.dl.sourceforge.net/project/qbittorrent/qbittorrent-win32/qbittorrent-{version}/qbittorrent_{version}_x64_setup.exe?viasf=1'
				break

	elif name == 'Blender':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			title = elem.get('title')
			if title and title == 'Download Blender for Windows Installer':
				url = elem.get('href')
				break

	elif name == 'OpenSSL':
		data = JSON.parse(data)
		vers = list(data['files'].keys())
		vers.reverse()

		for i in vers:
			if i.startswith('Win64OpenSSL-') and i.endswith('msi'):
				url = data['files'][i]['url']
				break

	elif name.startswith('Blender'):
		a_elems = soup.find_all('a')

		for elem in a_elems:
			text = elem.text
			if text and text == 'Windows – Installer':
				url = elem.get('href')
				ver = url.split('blender-', 1)[1].split('-', 1)[0]
				major = ver.rsplit('.', 1)[0]
				url = f'https://ftp.nluug.nl/pub/graphics/blender/release/Blender{major}/blender-{ver}-windows-x64.msi'
				break

	elif name == 'WinSCP':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			url = elem.get('href')
			if url and url.startswith('/download/WinSCP'):
				version = url.split('-', 2)[1]
				url = f'https://deac-riga.dl.sourceforge.net/project/winscp/WinSCP/{version}/WinSCP-{version}-Setup.msi?viasf=1'
				break

	elif name == 'ExifTool':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			href = elem.get('href')
			if href and '_64.zip' in href:
				url = f'https://exiftool.org/{href}'
				break

	else: return

	if not url:
		log.warning(f'[{name}] Didn\'t find any URL')
	else:
		log.debug(f'[{name}] Parsed best URL: {url}')

	return (name, url)

async def update_progs(progmap, session):
	tasks = []
	for prog in github_map:
		tasks.append(parse_prog(name = prog, github = True, session = session))

	for prog, slug in jetbrains_progs.items():
		tasks.append(parse_prog(slug, prog, session, jetbrains = True))

	for prog, url in parse_map.items():
		tasks.append(parse_prog(url, prog, session))

	results = await asyncio.gather(*tasks)
	parsed_data = [result for result in results if isinstance(result, tuple)]
	print()

	new = []
	for prog, url in parsed_data:
		if not url:
			print(f'Skipping: {prog}')

		elif progmap['urls'].get(prog) != url:
			progmap['urls'][prog] = url
			new.append([prog, url])

	return progmap, new

def push(repo: Repo, file, commit_msg):
	repo.git.add([file])
	repo.index.commit(commit_msg)
	repo.remotes.origin.push()

async def main(repo: Repo):
	a.start()
	repo.remotes.origin.pull()

	# input(JSON.stringify(progmap, indent = 2))
	# input(progmap_to_txt(progmap))

	a.lap('Preparing session...')
	async with niquests.AsyncSession(pool_connections = 100, pool_maxsize = 100) as session:
		a.lap('Fetching progmap...')
		progmap = await parse_github_urls(session)
		a.stop()
		progmap, new = await update_progs(progmap, session)

	# input(JSON.stringify(progmap, indent = 2))

	if not new:
		print('🆗 Everything is Up-To-Date!\n')
		return

	new_read = ', '.join(f'{prog}' for prog, _ in new)
	print(f'🔄️ New: {"\n".join(f"{prog}: {url}" for prog, url in new)}\n')

	txt = progmap_to_txt(progmap)
	# input(txt)

	await aio.open(urls_path, 'write', 'w', txt)
	commit_msg = f'Update urls.txt: {new_read}'

	# input('\nPress any key to push . . . ')
	push(repo, 'urls.txt', commit_msg)
	print('✅ Pushed successfully\n')

if __name__ == '__main__':
	enhance_loop()
	a = Anim('Pulling repository...', chars = AnimChars.slash, delay = 0.2)

	while True:
		print(f'[{datetime.now()}]')
		asyncio.run(main(repo))
		if not a.done:
			a.stop()

		# print(gtihub_node.to_ready_typing())
		time.sleep(3600)