from playwright.sync_api import sync_playwright
from database import get_setting

def publish_post(title, content, media_path=None, chapeu="Notícias"):
    """
    Usa o Playwright para abrir o navegador, logar no painel admin e publicar a matéria.
    """
    SITE_USERNAME = get_setting('site_user', 'Alyson')
    SITE_PASSWORD = get_setting('site_pass', '')
    SITE_ADMIN_URL = "https://leiasb.com.br/wp-admin/post-new.php"
    
    if not SITE_PASSWORD:
        print("Erro: Usuário ou senha do site não configurados no banco de dados!")
        return False
        
    print("Iniciando o robô de postagem (Playwright)...")
    
    try:
        with sync_playwright() as p:
            # headless=True é OBRIGATÓRIO no Render (servidor na nuvem não tem tela gráfica)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Acessando: {SITE_ADMIN_URL}")
            page.goto(SITE_ADMIN_URL)
            
            # --- TENTATIVA DE LOGIN ---
            print("Tentando fazer login...")
            try:
                # Preenche usuário
                user_input = page.locator("input[name='log'], input[id='user_login'], input[name='usuario'], input[name='username'], input[name='login'], input[type='email'], input[type='text']").first
                user_input.fill(SITE_USERNAME)
            except Exception as login_err:
                print("--- ERRO AO ACHAR CAMPO DE LOGIN ---")
                print(f"URL atual: {page.url}")
                print(f"Título da página: {page.title()}")
                print("Primeiras linhas do site (para descobrirmos se fomos bloqueados):")
                print(page.content()[:1500])
                raise login_err
            
            # Preenche senha
            pass_input = page.locator("input[name='pwd'], input[id='user_pass'], input[type='password']").first
            pass_input.fill(SITE_PASSWORD)
            
            # Clica no botão de entrar
            login_btn = page.locator("input[name='wp-submit'], button[type='submit'], input[type='submit'], button:has-text('Entrar'), button:has-text('Login')").first
            login_btn.click()
            
            page.wait_for_load_state('networkidle')
            print("Login possivelmente concluído.")
            
            # --- TENTATIVA DE POSTAGEM ---
            print("Tentando criar a postagem (aba Notícia -> Cadastrar notícia)...")
            try:
                # 1. Clica na aba 'noticia'
                print("Procurando aba 'Notícia'...")
                # Regex ignorando maiúsculas e minúsculas e aceitando com ou sem acento
                page.locator("text=/[Nn]ot[íi]cia/").first.click(force=True, timeout=5000)
                page.wait_for_timeout(2000) # Pequena pausa para o menu abrir (se tiver animação)
                
                # 2. Clica em 'cadastrar noticia'
                print("Procurando botão 'Cadastrar notícia'...")
                page.locator("text=/[Cc]adastrar [Nn]ot[íi]cia/").first.click(force=True, timeout=5000)
                page.wait_for_load_state('networkidle')
                
                # Preenche título (tenta seletores comuns)
                page.locator("input[name='titulo'], input[name='title'], input#title").first.fill(title, timeout=5000)
                
                # Preenche Chapéu e Subtítulo
                try:
                    page.locator("input[name*='chapeu'], input[name*='hat']").first.fill(chapeu, timeout=3000)
                except:
                    pass
                    
                try:
                    page.locator("input[name*='subtitulo'], textarea[name*='subtitulo']").first.fill(content[:50] + "...", timeout=3000)
                except:
                    pass

                # Preenche Categoria
                print("Preenchendo categoria...")
                try:
                    # Como vemos na imagem, Categoria é o segundo campo de select (índice 1 no nth)
                    page.locator("select").nth(1).select_option(index=1, force=True, timeout=3000)
                except Exception as e:
                    print("Aviso na Categoria:", e)

                # Preenche conteúdo (Texto) garantindo que o TinyMCE registre a mudança
                # Preenche conteúdo (Texto) garantindo que o HTML renderize corretamente
                print("Preenchendo texto...")
                try:
                    # Injeta o HTML diretamente no corpo do iframe (funciona sem depender do objeto tinymce global)
                    page.frame_locator('iframe#mce_0_ifr, iframe[title*="Rich Text Area"]').locator('body').evaluate('(body, html) => body.innerHTML = html', content)
                except Exception as e:
                    print("Erro no iframe do TinyMCE. Tentando fallback...")
                    try:
                        # Fallback injetando innerHTML na div editável
                        area = page.locator(".note-editable, .ql-editor, [contenteditable='true']").first
                        area.evaluate('(el, html) => el.innerHTML = html', content)
                    except Exception as fallback_e:
                        print("Erro ao preencher texto (fallback):", fallback_e)
                
                # Envia Foto de Capa
                if media_path:
                    try:
                        print("Enviando Foto de capa...")
                        # O input file costuma ser genérico
                        page.locator("input[type='file']").first.set_input_files(media_path, timeout=5000)
                        print("Foto selecionada com sucesso!")
                    except Exception as e:
                        print(f"AVISO: Ocorreu um erro ao tentar enviar a foto. {e}")
                        
                # Ativa os botões de Instagram e Story
                print("Ativando postagem no Instagram e Stories...")
                try:
                    cb = page.locator("input[name*='insta'][type='checkbox'], input[id*='insta'][type='checkbox'], input.check-post-plinsta").first
                    if cb.count() > 0:
                        cb.evaluate("el => { if(!el.checked) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true})); } }")
                    else:
                        page.locator("text=Publicar como post?").last.locator("xpath=..").click(force=True, timeout=2000)
                            
                    # Força o preenchimento da legenda mesmo se estiver invisível
                    legenda_text = "Saiba mais acessando nosso portal de notícias: Jornal Leia SB"
                    legenda_box = page.locator("textarea[name*='legenda'], textarea").last
                    if legenda_box.count() > 0:
                        legenda_box.evaluate(f'(el) => el.value = "{legenda_text}"')
                except Exception as e:
                    print("Aviso ao ativar post no feed/legenda:", str(e).encode('cp1252', errors='ignore').decode('cp1252'))
                    
                try:
                    cb = page.locator("input[name*='storie'][type='checkbox'], input[id*='storie'][type='checkbox'], input.check-storie-plinsta").first
                    if cb.count() > 0:
                        cb.evaluate("el => { if(!el.checked) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true})); } }")
                    else:
                        page.locator("text=Publicar como storie?").last.locator("xpath=..").click(force=True, timeout=2000)
                except Exception as e:
                    print("Aviso ao ativar storie:", str(e).encode('cp1252', errors='ignore').decode('cp1252'))
                    
                try:
                    cb = page.locator("input[name*='notifica'][type='checkbox'], input[id*='notifica'][type='checkbox']").first
                    if cb.count() > 0:
                        cb.evaluate("el => { if(!el.checked) { el.checked = true; el.dispatchEvent(new Event('change', {bubbles: true})); } }")
                    else:
                        page.locator("text=Enviar notificação?").last.locator("xpath=..").click(force=True, timeout=2000)
                except Exception as e:
                    print("Aviso ao ativar notificacao:", str(e).encode('cp1252', errors='ignore').decode('cp1252'))
                        
                # Clica EXATAMENTE no botão de Publicar
                publish_btn = page.locator("button:has-text('Publicar'), input[value='Publicar'], button[name='publicar'], input[type='submit']").last
                publish_btn.click(force=True, no_wait_after=True, timeout=5000)
                
                print("Botão de publicar clicado com sucesso!")
                # Espera um pouco para garantir que a requisição foi feita
                page.wait_for_timeout(3000)
                
            except Exception as e:
                print(f"\nAVISO: Não foi possível realizar a postagem automática.")
                print(f"Os botões ou campos do seu painel não bateram com a nossa tentativa genérica.")
                print(f"Erro: {e}")
            
            safe_title = title.encode('cp1252', errors='ignore').decode('cp1252')
            print(f"\nTítulo que tentamos postar: {safe_title}")
            
            # Deixa aberto por uns segundos para você ver
            page.wait_for_timeout(10000)
            
            browser.close()
            return True
            
    except Exception as e:
        print(f"Erro no Playwright: {e}")
        return False

if __name__ == "__main__":
    publish_post("Título Teste", "Conteúdo teste")
