import sys
from playwright.sync_api import sync_playwright
from database import get_setting

def delete_post(title_to_delete):
    SITE_USERNAME = get_setting('site_user', 'Alyson')
    SITE_PASSWORD = get_setting('site_pass', '')
    SITE_ADMIN_URL = "https://leiasb.com.br/wp-admin/edit.php"
    
    if not SITE_PASSWORD:
        print("Erro: Usuário ou senha não configurados.")
        return False

    print(f"Iniciando robô lixeiro para apagar: {title_to_delete}...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Login
            print("Fazendo login no WordPress...")
            page.goto("https://leiasb.com.br/wp-login.php", timeout=60000)
            page.fill("input[name='log']", SITE_USERNAME)
            page.fill("input[name='pwd']", SITE_PASSWORD)
            page.click("input[name='wp-submit']")
            page.wait_for_load_state("networkidle")
            
            # Vai para a lista de posts
            page.goto(SITE_ADMIN_URL, timeout=60000)
            
            # Pesquisa o post exato
            print("Pesquisando o post...")
            page.fill("input[id='post-search-input']", title_to_delete)
            page.click("input[id='search-submit']")
            page.wait_for_load_state("networkidle")
            
            # Verifica se encontrou algo
            # Procura pela linha do post cujo título contém o texto buscado
            row_locator = page.locator(f"tr.iedit:has-text(\"{title_to_delete[:20]}\")").first
            
            if row_locator.count() > 0:
                print("Post encontrado! Excluindo...")
                # O WordPress esconde os links de ação até passar o mouse
                row_locator.hover()
                
                # Clica em colocar na lixeira
                trash_btn = row_locator.locator("a.submitdelete")
                if trash_btn.count() > 0:
                    trash_btn.click()
                    page.wait_for_load_state("networkidle")
                    print("Post movido para a lixeira com sucesso!")
                    browser.close()
                    return True
                else:
                    print("Botão de lixeira não encontrado na linha.")
            else:
                print("Nenhum post correspondente encontrado na busca.")
                
            browser.close()
            return False
            
    except Exception as e:
        print(f"Erro inesperado no robô lixeiro: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        title = sys.argv[1]
        delete_post(title)
    else:
        print("Forneça o título do post para deletar.")
