import argparse

import re

import logging
from urlparse import urljoin

import requests
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
}
MAX_REDIRECTS = 3


logger = logging.getLogger(__name__)
YOGASITE_HOMEPAGE = 'https://yogasite.org'


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', help="Yoga site username", required=True)
    parser.add_argument('-a', '--admin', help="Yoga site admin field", required=True)
    parser.add_argument('-p', '--password', help="Yoga site password", required=True)
    parser.add_argument('-o', '--output', default="dump.zip", help="Output dump filename")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = get_args()

    data = {
        'pwd': args.password,
        'admin': args.admin,
        'username': args.user,
        'login': 'Log-in',
    }

    session = requests.session()
    session.max_redirects = MAX_REDIRECTS
    session.headers = HEADERS

    # Load the homepage to get the relevant session cookies
    homepage = session.get(YOGASITE_HOMEPAGE)
    logger.info("Login to website")
    login = session.post(YOGASITE_HOMEPAGE, data=data, allow_redirects=False)

    # Yoga site redirect on succesful login
    is_login_successfull = login.status_code == 302
    if not is_login_successfull:
        logger.error("Unable to login into yogasite.org with username: {}. Please check the credentials provided".format(args.user))
        sys.exit()

    logger.info("Create new mysql dump")
    # This request will be blocking until the backup is ready
    create_mysql_dump = session.get(urljoin(YOGASITE_HOMEPAGE, '/admin_admin/mysqldump.php'))
    if not create_mysql_dump.status_code == 200:
        logger.error("Failed to inititate the sql dump back")
        sys.exit()

    logger.info("Find the newly created dump zip")
    # Now, locate the download link from the backup.php page
    backup_page = session.get(urljoin(YOGASITE_HOMEPAGE, '/admin_admin/backup.php'))
    if not backup_page.status_code == 200:
        logger.error("Failed getting the backup page while looking for the dump download link")
        sys.exit()

    download_link = re.findall("\.\.(.+?\.zip)", backup_page.content)
    if not download_link:
        logger.error("Unable to find the zip download from the backup page")
        sys.exit()

    download_link = urljoin(YOGASITE_HOMEPAGE, download_link[0])

    logger.info("Download mysql dump from: {}".format(download_link))
    dump_stream = session.get(download_link, stream=True)
    if not dump_stream.status_code == 200:
        logger.error("Unable to download dump file from: {}".format(download_link))
        sys.exit()

    with open(args.output, 'wb') as handle:
        for block in dump_stream.iter_content(1024):
            handle.write(block)
    logger.info("##### SUCCESS: Dump saved to: {}".format(args.output))
    logger.info("Done.")