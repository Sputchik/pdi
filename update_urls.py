from sputchedtools import aio, enhance_loop
from datetime import datetime
from bs4 import BeautifulSoup
from git import Repo

import aiohttp, asyncio, json, os, time

cwd = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/') + '/'
urls_path = cwd + 'urls.txt'
github_latest_draft = 'https://api.github.com/repos/{}/{}/releases/latest' # Owner, Repo Slug
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
}

parse_map = {
	'RegistryFinder': 'https://registry-finder.com/',
	'Go': 'https://go.dev/dl/?mode=json',
	'Gradle': 'https://gradle.org/releases/',
	'Google_Earth_Pro': 'https://support.google.com/earth/answer/168344?hl=en#zippy=%2Cdownload-a-google-earth-pro-direct-installer',
	'Git': 'https://git-scm.com/downloads/win',
	'Wireless Bluetooth': 'https://www.intel.com/content/www/us/en/download/18649/intel-wireless-bluetooth-drivers-for-windows-10-and-windows-11.html',
	'Python': 'https://www.python.org/downloads/',
	'Node.js': 'https://nodejs.org/en',
	'NVCleanstall': 'https://nvcleanstall.net/download',
	'K-Lite Codec': 'https://www.codecguide.com/download_k-lite_codec_pack_standard.htm',
	'Everything': 'https://www.voidtools.com/',
	'qBitTorrent': 'https://www.qbittorrent.org/download',
	'Librewolf': 'https://librewolf.net/installation/windows/',
	'Blender': 'https://www.blender.org/download/',
}

if not os.path.exists('token'):
	access_token = input('Github Access Token: ')
	open('token', 'w').write(access_token)

else:
	access_token = open('token', 'r').read()

remote_url = f"https://{access_token}@github.com/Sputchik/pdi.git"
os.chdir(cwd)
repo = Repo(cwd)
repo.remotes.origin.set_url(remote_url)

github_headers = {
	'Authorization': f'Bearer {access_token}'
}
remote_url = 'https://github.com/Sputchik/pdi.git'

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

	progs_lines = lines[cat_progs_start:cat_progs_end]

	for line in progs_lines:
		cat, progs = line.split('=')
		progs = sorted(progs.split(';'))
		cat_map[cat] = ';'.join(progs)

	return cat_map, '\n'.join(lines[ext_start:ext_end])

async def parse_github_urls() -> dict:
	response = await aio.request(urls_link, toreturn = 'text+status')
	data, status = response

	if status != 200:
		print(f'Fail: Github urls fetch: {urls_link}')
		return

	lines: list[str] = data.splitlines()
	url_index = get_line_index(lines, 'url_')
	url_lines = lines[url_index:]
	
	cats, exts = parse_categories(lines)

	progmap = {
		'cats': cats,
		'exts': exts,
		'urls': dict(sorted({
			line.split('url_')[1].split('=')[0].replace('^', ' '): line.split('=', maxsplit = 1)[1] for line in url_lines
		}.items(), key = lambda x: (x[0].lower(), x[1:])))
	}

	return progmap

def progmap_to_txt(progmap):
	first_line = 'Categories=' + ';'.join(list(progmap['cats'].keys()))
	cat_progs = '\n'.join([f"{key}={value}" for key, value in progmap['cats'].items()])
	urls = '\n'.join([f"url_{key.replace(' ', '^')}={value}" for key, value in progmap['urls'].items()])
	
	del progmap['cats']
	del progmap['urls']
	
	result = '\n\n'.join((first_line, cat_progs, *progmap.values(), urls))
	return result

def extract_versions(versions: dict[str, str]) -> str:
	preferred_exe = None
	selected_exe = False
	preferred_msi = None

	for key in versions:
		if key.endswith('.msi') and 'arm' not in key:
			# Check if it's a preferred '64' version
			if '64' in key:
				preferred_msi = key
				break
			elif '32' in key and not preferred_msi:
				preferred_msi = key
			elif not preferred_msi:
				preferred_msi = key

		elif key.endswith('.exe') and 'arm' not in key:
			# Check if it's a preferred '64' version
			if '64' in key and not selected_exe:
				preferred_exe = key
				selected_exe = True
			elif '32' in key and not preferred_exe:
				preferred_exe = key
			elif not preferred_exe:
				preferred_exe = key

	preferred_key = preferred_msi if preferred_msi else preferred_exe
	return preferred_key

async def direct_from_github(owner: str, project: str) -> str:
	url = github_latest_draft.format(owner, project)

	response = await aio.request(
		url,
		toreturn = 'json+status',
		headers = github_headers,
	)
	data, status = response

	print(f'{status}: {project}')

	if status != 200 or not isinstance(data, dict) or 'assets' not in data:
		print(f'Fail: Github latest version for `{project}`: {url}')
		return

	assets = data['assets']
	version_map = {unpack['name']: unpack['browser_download_url'] for unpack in assets}
	key = extract_versions(version_map)

	if not key:
		print(f'Fail: Github key version extraction: {url}')

	return version_map[key]

async def parse_prog(url = None, name = None, session = None):

	try:
		author, project = github_map[name]
		return (name, await direct_from_github(author, project))
	except KeyError:
		pass

	response = await aio.request(url, toreturn = 'text+status', session = session)
	data, status = response

	print(f'{status}: {name} - {url}')
	if status != 200:
		return

	if name == 'Go':
		version = json.loads(data)[0]['version'].split('go')[1]
		url = f'https://go.dev/dl/go{version}.windows-amd64.msi'

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

	elif name == 'Wireless Bluetooth':
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
		a_elems = soup.find_all('b')

		for elem in a_elems:
			a = elem.find('a')
			if a:
				version = a.text
				url = f'https://nodejs.org/dist/{version}/node-{version}-x64.msi'
				break

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
				version = elem.text.split(' ')[2]
				url = f'https://netcologne.dl.sourceforge.net/project/qbittorrent/qbittorrent-win32/qbittorrent-{version}/qbittorrent_{version}_x64_setup.exe?viasf=1'
				break
	
	elif name == 'Librewolf':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			url = elem.get('href')
			if url and url.startswith('https://gitlab.com/'):
				break
	
	elif name == 'Blender':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			title = elem.get('title')
			if title and title == 'Download Blender for Windows Installer':
				url = elem.get('href')
				break
	
	elif name == 'Git':
		a_elems = soup.find_all('a')

		for elem in a_elems:
			text = elem.text
			if text and text == '64-bit Git for Windows Setup':
				url = elem.get('href')
				break

	else: return

	return (name, url)

async def update_progs(progmap, session = None):
	tasks = []
	for prog in github_map:
		tasks.append(parse_prog(name = prog))

	for prog, url in parse_map.items():
		tasks.append(parse_prog(url, prog, session))

	results = await asyncio.gather(*tasks)
	parsed_data = ((result[0], result[1]) for result in results if isinstance(result, tuple))
	print()

	new = False
	for prog, url in parsed_data:
		if progmap['urls'][prog] != url:
			progmap['urls'][prog] = url
			print(f'New: {prog}')
			new = True

	return progmap, new

def push(repo: Repo, file):
	repo.git.add([file])
	repo.index.commit('Update urls.txt')
	repo.remotes.origin.push()

async def main(repo: Repo):
	repo.remotes.orrigin.pull()

	progmap = await parse_github_urls()
	# input(json.dumps(progmap, indent = 2))

	async with aiohttp.ClientSession() as session: progmap, new = await update_progs(progmap, session = session)
	# input(json.dumps(progmap, indent = 2))

	if not new:
		print('Everything is Up-To-Date!\n')
		return
	
	txt = progmap_to_txt(progmap)
	# input(txt)

	await aio.open(urls_path, 'write', 'w', txt)

	# input('\nPress any key to push . . . ')
	push(repo, 'urls.txt')
	print('Pushed successfully\n')

if __name__ == '__main__':
	enhance_loop()
	
	while True:
		print(f'[{datetime.now()}]')
		asyncio.run(main(repo))
		time.sleep(3600)
