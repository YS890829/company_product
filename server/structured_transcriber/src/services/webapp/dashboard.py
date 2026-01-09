"""
Streamlit Dashboard for Transcription Search and Meeting Management

This module provides a web-based UI for:
- Searching transcriptions with semantic search
- Browsing meeting list and details
- Q&A interface using RAG
- Statistics and visualizations
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# ==================== Configuration ====================

API_BASE_URL = "http://localhost:8001"

st.set_page_config(
    page_title="Meeting Transcription Dashboard",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Helper Functions ====================

def check_api_health() -> bool:
    """Check if API server is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def search_transcriptions(query: str, n_results: int = 5, meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Call search API endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/search",
            json={"query": query, "n_results": n_results, "meeting_id": meeting_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"検索エラー: {str(e)}")
        return None


def list_meetings(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Call meetings list API endpoint"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/meetings",
            params={"limit": limit, "offset": offset},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"ミーティング一覧取得エラー: {str(e)}")
        return []


def get_meeting_detail(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Call meeting detail API endpoint"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/meetings/{meeting_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"ミーティング詳細取得エラー: {str(e)}")
        return None


def ask_question(question: str, n_context: int = 5, meeting_id: Optional[str] = None) -> Dict[str, Any]:
    """Call Q&A API endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/qa",
            json={"question": question, "n_context": n_context, "meeting_id": meeting_id},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Q&Aエラー: {str(e)}")
        return None


# ==================== UI Components ====================

def render_search_result(result: Dict[str, Any]):
    """Render a single search result"""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"**{result['speaker']}**: {result['text']}")

        with col2:
            if result.get('timestamp'):
                st.caption(f"🕒 {result['timestamp']}")

        with col3:
            score = result['relevance_score']
            st.caption(f"📊 {score:.2%}")

        st.caption(f"📁 {result['file_name']} (ID: {result['meeting_id']})")
        st.divider()


def render_meeting_card(meeting: Dict[str, Any]):
    """Render a meeting summary card"""
    with st.container():
        st.subheader(f"📄 {meeting['file_name']}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("作成日時", meeting['created_at'][:10])

        with col2:
            st.metric("セグメント数", meeting['total_segments'])

        with col3:
            st.metric("話者数", meeting['total_speakers'])

        with col4:
            duration = meeting.get('duration_minutes')
            if duration:
                st.metric("時間", f"{duration:.1f}分")
            else:
                st.metric("時間", "N/A")

        if st.button("詳細を表示", key=f"detail_{meeting['meeting_id']}"):
            st.session_state.selected_meeting = meeting['meeting_id']
            st.session_state.page = "meeting_detail"
            st.rerun()

        st.divider()


def render_segment(segment: Dict[str, Any]):
    """Render a single transcript segment"""
    with st.container():
        col1, col2 = st.columns([1, 5])

        with col1:
            st.caption(f"🕒 {segment.get('timestamp', 'N/A')}")
            st.caption(f"🗣️ {segment['speaker']}")

        with col2:
            st.markdown(segment['text'])

        st.divider()


# ==================== Main Pages ====================

def page_search():
    """Search page"""
    st.title("🔍 セマンティック検索")

    # Search form
    with st.form("search_form"):
        query = st.text_input(
            "検索クエリを入力してください",
            placeholder="例: プロジェクトの進捗について"
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            meeting_filter = st.text_input(
                "ミーティングIDでフィルタ（オプション）",
                placeholder="例: meeting_20240101_120000"
            )

        with col2:
            n_results = st.slider("結果数", 1, 20, 5)

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            search_button = st.form_submit_button("🔍 検索", use_container_width=True)

    # Execute search
    if search_button and query:
        with st.spinner("検索中..."):
            meeting_id = meeting_filter if meeting_filter else None
            results = search_transcriptions(query, n_results, meeting_id)

            if results:
                st.success(f"✅ {results['total_results']}件の結果が見つかりました（処理時間: {results['processing_time_ms']:.1f}ms）")

                st.divider()
                st.subheader("検索結果")

                for result in results['results']:
                    render_search_result(result)
            else:
                st.warning("結果が見つかりませんでした")


def page_meetings():
    """Meetings list page"""
    st.title("📋 ミーティング一覧")

    # Controls
    col1, col2 = st.columns([1, 4])

    with col1:
        limit = st.selectbox("表示件数", [10, 25, 50, 100], index=2)

    # Load meetings
    with st.spinner("ミーティング一覧を取得中..."):
        meetings = list_meetings(limit=limit)

    if meetings:
        st.info(f"📊 {len(meetings)}件のミーティングが見つかりました")

        for meeting in meetings:
            render_meeting_card(meeting)
    else:
        st.warning("ミーティングが見つかりませんでした")


def page_meeting_detail():
    """Meeting detail page"""
    if 'selected_meeting' not in st.session_state:
        st.warning("ミーティングが選択されていません")
        if st.button("ミーティング一覧に戻る"):
            st.session_state.page = "meetings"
            st.rerun()
        return

    meeting_id = st.session_state.selected_meeting

    # Back button
    if st.button("⬅️ ミーティング一覧に戻る"):
        st.session_state.page = "meetings"
        st.rerun()

    # Load meeting detail
    with st.spinner("ミーティング詳細を取得中..."):
        meeting = get_meeting_detail(meeting_id)

    if not meeting:
        st.error("ミーティングが見つかりませんでした")
        return

    # Header
    st.title(f"📄 {meeting['file_name']}")

    # Metadata
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("ミーティングID", meeting['meeting_id'])

    with col2:
        st.metric("作成日時", meeting['created_at'][:10])

    with col3:
        st.metric("セグメント数", meeting['total_segments'])

    # Participants
    st.subheader("👥 参加者")
    st.write(", ".join(meeting['participants']))

    st.divider()

    # Transcript
    st.subheader("📝 文字起こし")

    for segment in meeting['segments']:
        render_segment(segment)


def page_qa():
    """Q&A page"""
    st.title("💬 Q&A（RAG）")

    st.info("ミーティングの内容について質問してください。AIが関連する発言を検索して回答します。")

    # Q&A form
    with st.form("qa_form"):
        question = st.text_area(
            "質問を入力してください",
            placeholder="例: プロジェクトの課題は何ですか？",
            height=100
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            meeting_filter = st.text_input(
                "ミーティングIDでフィルタ（オプション）",
                placeholder="例: meeting_20240101_120000"
            )

        with col2:
            n_context = st.slider("コンテキスト数", 1, 10, 5)

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            ask_button = st.form_submit_button("💬 質問する", use_container_width=True)

    # Execute Q&A
    if ask_button and question:
        with st.spinner("回答を生成中..."):
            meeting_id = meeting_filter if meeting_filter else None
            result = ask_question(question, n_context, meeting_id)

            if result:
                st.success(f"✅ 回答生成完了（処理時間: {result['processing_time_ms']:.1f}ms）")

                st.divider()

                # Answer
                st.subheader("💡 回答")
                st.markdown(result['answer'])

                st.divider()

                # Context
                with st.expander(f"📚 参照したコンテキスト（{len(result['context_chunks'])}件）"):
                    for chunk in result['context_chunks']:
                        render_search_result(chunk)


def page_stats():
    """Statistics page"""
    st.title("📊 統計情報")

    st.info("統計機能は今後実装予定です")

    # Load meetings for basic stats
    with st.spinner("データを取得中..."):
        meetings = list_meetings(limit=100)

    if meetings:
        # Convert to DataFrame
        df = pd.DataFrame(meetings)

        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総ミーティング数", len(meetings))

        with col2:
            total_segments = df['total_segments'].sum()
            st.metric("総セグメント数", f"{total_segments:,}")

        with col3:
            avg_speakers = df['total_speakers'].mean()
            st.metric("平均話者数", f"{avg_speakers:.1f}")

        with col4:
            if 'duration_minutes' in df.columns:
                total_duration = df['duration_minutes'].sum()
                st.metric("総時間", f"{total_duration:.0f}分")

        st.divider()

        # Table
        st.subheader("ミーティング一覧")
        st.dataframe(
            df[['file_name', 'created_at', 'total_segments', 'total_speakers']],
            use_container_width=True
        )


# ==================== Main App ====================

def main():
    """Main application"""

    # Check API health
    if not check_api_health():
        st.error("⚠️ APIサーバーに接続できません。`src/webapp/api_server.py`が起動していることを確認してください。")
        st.code("python src/webapp/api_server.py", language="bash")
        return

    # Sidebar navigation
    with st.sidebar:
        st.title("🎙️ Transcription Dashboard")

        page = st.radio(
            "ナビゲーション",
            ["search", "meetings", "qa", "stats"],
            format_func=lambda x: {
                "search": "🔍 検索",
                "meetings": "📋 ミーティング一覧",
                "qa": "💬 Q&A",
                "stats": "📊 統計"
            }[x],
            key="page_selector"
        )

        # Override with session state if set
        if 'page' in st.session_state:
            page = st.session_state.page
            del st.session_state.page

        st.divider()

        # API status
        st.caption("API Status")
        st.success("✅ 接続済み")

    # Render selected page
    if page == "search":
        page_search()
    elif page == "meetings":
        page_meetings()
    elif page == "meeting_detail":
        page_meeting_detail()
    elif page == "qa":
        page_qa()
    elif page == "stats":
        page_stats()


if __name__ == "__main__":
    main()
